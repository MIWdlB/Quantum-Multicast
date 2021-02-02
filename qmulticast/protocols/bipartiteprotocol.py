"""Defines the protocol to be followed at a node bipartite source(s)"""
import logging
import operator
from functools import reduce
from typing import Optional, List

from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol
from netsquid.protocols.protocol import Signals
from netsquid.qubits.qubitapi import fidelity, reduced_dm
from netsquid.components.component import Port
from netsquid.components.qprogram import QuantumProgram
from netsquid.components.instructions import INSTR_X

from qmulticast.programs import CreateGHZ
from qmulticast.utils import gen_GHZ_ket

logger = logging.getLogger(__name__)

handler = logging.FileHandler(filename="fidelity-data.txt", mode="w")

res_logger = logging.Logger(name="results")
res_logger.addHandler(handler)


class BipartiteProtocol(NodeProtocol):
    """Class defining the protocol of a bipartite network node.

    If the node is a source, send out entangled qubits and transform to GHZ.
    If the node is a reciever, await incoming qubit and classical message.
    """

    def __init__(
        self,
        node: Node,
        name: Optional[str] = None,
        source: bool = False,
        receiver: bool = True,
    ):
        """Initialise the protocol wiht information about the node.

        Parameters
        ----------
        node : Node
            The node on which to run this protocol.
        name : Optional[str]
            The name of this protocol.
        source : bool, default = True
            Whether this node should act as a source.
            If not the node is a reciever.
        """
        logger.debug(f"Initialising Bipartite protocol for node {node.name}.")
        super().__init__(node=node, name=name)

        self._output = source
        self._input = receiver

        if self._output:
            self.add_subprotocol(BipartiteOutputProtocol(self.node))

        if self._input:
            self.add_subprotocol(BipartiteInputProtocol(self.node))

    def run(self):
        """Run the protocol."""
        node = self.node
        logger.debug(f"Running bipartite protocol on node {node.name}.")
        self.start_subprotocols()


class BipartiteInputProtocol(NodeProtocol):
    """ Defines behviour needed when a source expects input qubits."""

    def __init__(self, node: Node, name: Optional[str] = None):
        super().__init__(node=node, name=name)

        mem_positions = self.node.qmemory.num_positions
        mem_ports = self.node.qmemory.ports
        self.q_in_ports = [mem_ports[f"qin{num}"] for num in range(1, mem_positions, 2)]

        self.c_in_ports = [
            port for port in self.node.ports.values() if "cin" in port.name
        ]
        for port in self.c_in_ports:
            self.add_subprotocol(ClassicalInputPortProtocol(node=self.node, port=port))

    def run(self):
        """Protocol for reciver."""
        # Get input
        logger.debug(f"Running Input protocol.")
        await_quantum_input = [self.await_port_input(port) for port in self.q_in_ports]

        self.start_subprotocols()

        while True:
            yield reduce(operator.or_, await_quantum_input)
            logger.debug(
                f"Got qubit input: memory useage {self.node.qmemory.used_positions}"
            )
            logger.debug(
                f"Node {self.node.name} used memory: {self.node.qmemory.used_positions}"
            )


class ClassicalInputPortProtocol(NodeProtocol):
    def __init__(self, node: Node, port: Port, name: Optional[str] = None) -> None:
        super().__init__(node=node, name=name)
        self.port = port

    def run(self) -> None:
        """Wait for input signal and delete qubit as appropriate."""
        logger.debug(f"Node {self.node.name} listening on {self.port.name}.")
        while True:
            yield self.await_port_input(self.port)
            message = self.port.rx_input()
            logger.debug("Node %s recieved message %s", self.node, message.items)
            edge = self.port.name.lstrip("cin-")
            matching_qubits = self.node.qmemory.get_matching_qubits("edge", value=edge)
            
            if f"GHZ Correction {edge}" in message.items:
                for qubit in matching_qubits:
                    prog = QuantumProgram()
                    prog.apply(INSTR_X, qubit)
                    self.node.qmemory.execute_program(prog)
                    logger.debug("Corrected qubit %s", qubit.name)

            if f"Delete qubit {edge}" in message.items:
                for qubit in matching_qubits:
                    logger.debug("Node %s deleting qubit %s", self.node.name, qubit)
                    self.node.qmemory.pop(qubit)


class BipartiteOutputProtocol(NodeProtocol):
    """Defines behaviour of node when outputting qubits"""

    def __init__(self, node: Node, name: Optional[str] = None):
        super().__init__(node=node, name=name)

        mem_positions = self.node.qmemory.num_positions
        mem_ports = self.node.qmemory.ports
        self.q_out_ports = [
            value for key, value in self.node.ports.items() if "qout" in key
        ]

        self.source_mem = [mem_ports[f"qin{num}"] for num in range(0, len(self.q_out_ports)*2, 2)]
        self.sources = [
            f"qsource-{port.name.lstrip('qout-')}" for port in self.q_out_ports
        ]

    def _trigger_all_sources(self) -> None:
        """Trigger all sources on the node."""
        logger.debug("Triggering all sources.")

        for source in self.sources:
            # Trigger the source
            self.node.subcomponents[source].trigger()
            logger.debug(f"Triggered source {source}.")

    def _send_all_delete(self) -> None:
        """Send a classical message to each reciever node."""
        logger.debug("Sending delete instruction to all nodes.")
        for port_name, port in self.node.ports.items():
            if "cout" in port_name:
                edge = port_name.lstrip("cout-")
                port.tx_output(f"Delete qubit {edge}")

    def _send_corrections(self, output: dict) -> None:
        """Send a classical message to correct for GHZ preparation."""
        logger.debug("Sending corrections to receivers.")
        for record, value in output.items():
            if "measure" in record:
                # If the measurement is 0 do nothing.
                if value == [0]:
                    continue

                qubit_no = int(record.lstrip("measure-"))
                qubit = self.node.qmemory.peek(qubit_no)[0]

                edgenodes = qubit.name.split("-")[1:3]
                edge_name = "-".join(edgenodes)

                self.node.ports[f"cout-{edge_name}"].tx_output(
                    f"GHZ Correction {edge_name}"
                )
                logger.debug("Sent correction %s on port cout-%s", value, edge_name)

    def run(self) -> None:
        """The protocol to be run by a source node."""
        logger.debug(f"Running Output protocol.")

        await_all_sources = [self.await_port_input(port) for port in self.source_mem]

        for index in range(10):
            print("index: ", index)
            self._trigger_all_sources()
            yield reduce(operator.and_, await_all_sources)
            logger.debug("Got all memory input from sources.")

            # Do entanglement
            bell_qubits = [
                pos for pos in self.node.qmemory.used_positions if pos % 2 == 0
            ]
            prog = CreateGHZ(bell_qubits)
            logger.debug(f"Executing program with qubits {bell_qubits}")
            self.node.qmemory.execute_program(prog)
            yield self.await_program(self.node.qmemory)
            logger.debug("Program complete, output %s.", prog.output)

            self._send_corrections(prog.output)

            #qubits = [self.node.qmemory.peek(pos)[0] for pos in bell_qubits]
            #fidelity_val = fidelity(qubits, gen_GHZ_ket(len(qubits)), squared=True)
            #logger.debug(f"Fidelity: {fidelity_val}")
            #logger.debug(f"Reduced dm of qubits: \n{reduced_dm(qubits)}")

            #self.send_signal(Signals.SUCCESS, fidelity_val)

            #self._send_all_delete()
            [self.node.qmemory.pop(index) for index in self.node.qmemory.used_positions]
            await_mem_busy = [
                self.await_mempos_busy_toggle(self.node.qmemory, [pos]) 
                for pos in range(0, len(self.q_out_ports)*2, 2)
            ]
            yield reduce(operator.and_, await_mem_busy)
            logger.debug("Memory positions not busy.")

            self._trigger_all_sources()

            # Test down here to see why it won't trigger.
            yield self.await_timer(1e5)
            self._trigger_all_sources()
            logger.debug("Test")
            #import pdb; pdb.set_trace()
            # It doesn't have anything n the memories...
            yield reduce(operator.and_, await_all_sources)
            print("wait for trigger done.")

