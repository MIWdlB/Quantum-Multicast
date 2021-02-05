"""Defines the protocol to be followed at a node bipartite source(s)"""
import logging
import operator
from functools import reduce
from typing import List, Optional

from netsquid.components.component import Port
from netsquid.components.instructions import INSTR_X
from netsquid.components.qprogram import QuantumProgram
from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol
from netsquid.protocols.protocol import Signals
from netsquid.qubits.qubitapi import fidelity, reduced_dm
from netsquid.util.simlog import get_loggers

from qmulticast.programs import CreateGHZ
from qmulticast.utils import fidelity_from_node, gen_GHZ_ket
from qmulticast.utils.functions import log_entanglement_rate

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
            self.add_subprotocol(BipartiteInputProtocol(self.node, name=f"input-{self.node.name}"))

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
        self.add_signal(label="recieved")

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
            self.send_signal("recieved")


class ClassicalInputPortProtocol(NodeProtocol):
    """For listening on classical ports. NOT IN USE."""
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

            if f"Delete qubit {edge}" in message.items:
                for qubit in matching_qubits:
                    logger.debug("Node %s deleting qubit %s", self.node.name, qubit)
                    self.node.qmemory.pop(qubit)


class BipartiteOutputProtocol(NodeProtocol):
    """Defines behaviour of node when outputting qubits"""

    def __init__(self, node: Node, name: Optional[str] = None):
        super().__init__(node=node, name=name)

        mem_ports = self.node.qmemory.ports
        self.q_out_ports = [
            value for key, value in self.node.ports.items() if "qout" in key
        ]

        self.source_mem = [
            mem_ports[f"qin{num}"] for num in range(0, len(self.q_out_ports) * 2, 2)
        ]
        self.sources = [
            f"qsource-{port.name.lstrip('qout-')}" for port in self.q_out_ports
        ]
        self.fidelity = fidelity_from_node(self.node)

    def _trigger_all_sources(self) -> None:
        """Trigger all sources on the node."""
        logger.debug("Triggering all sources.")
        self.triggered = {source: False for source in self.sources}

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

    def _do_corrections(self, output: dict) -> None:
        """Correct qubits for GHZ state creation."""
        logger.debug("Completing corrections.")
        network = self.node.supercomponent

        for record, value in output.items():
            if "measure" in record:
                # If the measurement is 0 do nothing.
                if value == [0]:
                    logger.debug("No correction for measure %s", record)
                    continue
                
                logger.debug("Correcting for measure %s", record)
                qubit_no = int(record.lstrip("measure-"))
                qubit = self.node.qmemory.peek(qubit_no)[0]

                edgenodes = qubit.name.split("-")[1:3]
                end_name = edgenodes[-1]
                edge_name = "-".join(edgenodes)

                end_qmemory = network.nodes[end_name].qmemory
                qubit = end_qmemory.get_matching_qubits("edge", value=edge_name)

                if len(qubit) == 0:
                    logger.warning("Could not find qubit on node %s", end_name)
                    logger.debug("Skipping run.")
                    continue

                end_qmemory.execute_instruction(
                    instruction = INSTR_X,
                    qubit_mapping = qubit,
                    physical = False
                )

                logger.debug("Completed correction on node %s", end_name)

    def transmission_time(self, port_name: str) -> None:
        """Wait for a qubit to be received at the end of a channel."""

        connection = self.node.ports[port_name].connected_port.component
        channel = connection.channel_AtoB

        delay = channel.compute_delay()
        logger.debug(f"Found transmission time {delay} for channel {channel.name}")

        return delay * 1.0000001

    def run(self) -> None:
        """The protocol to be run by a source node."""
        logger.debug(f"Running Output protocol.")

        while True:

            await_all_sources = [
                self.await_port_input(port) for port in self.source_mem
            ]
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

            # TODO how do we find the minimum wait time needed in a sensible way?
            # Could await on ports using
            #self.node.subcomponents['qsource-edge'].ports['qout1'].connected_port
            await_recieved = [
                self.await_timer(self.transmission_time(port_name))
                for port_name in self.node.ports
                if "qout" in port_name
            ]
            logger.debug("Waiting transmission time.")
            yield reduce(operator.and_, await_recieved)
            self._do_corrections(prog.output)

            next(self.fidelity)

            # self._send_all_delete()
            logger.debug("Clearing local memory.")
            self.node.qmemory.reset()