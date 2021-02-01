"""Defines the protocol to be followed at a node bipartite source(s)"""
import logging
import operator
from functools import reduce
from typing import Optional

from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol
from netsquid.protocols.protocol import Signals
from netsquid.qubits.qubitapi import fidelity, reduced_dm
from netsquid.components.component import Port

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
        recipient: bool = True,
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
        self._input = recipient

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

        self.c_in_ports = [port for port in self.node.ports.values() if "cin" in port.name]
        for port in self.c_in_ports:
            self.add_subprotocol(DeleteQubitProtocol(node=self.node, port=port))

    def run(self):
        """Protocol for reciver."""
        # Get input
        logger.debug(f"Running Input protocol.")
        await_quantum_input = [
            self.await_port_input(port) for port in self.q_in_ports
        ]

        self.start_subprotocols()

        while True:
            yield reduce(operator.or_, await_quantum_input)

            logger.debug(f"Got input: memory useage {self.node.qmemory.used_positions}")
            logger.debug(
                f"Node {self.node.name} used memory: {self.node.qmemory.used_positions}"
            )

class DeleteQubitProtocol(NodeProtocol):
    def __init__(self,node: Node, port: Port, name: Optional[str] = None) -> None:
        super().__init__(node=node, name=name)
        self.port = port

    def run(self) -> None:
        """Wait for input signal and delete qubit as appropriate."""
        logger.debug(f"Node {self.node.name} listening for delete instructions.")
        while True:
            yield self.await_port_input(self.port)
            message = self.port.rx_input()
            edge = self.port.name.lstrip("cin-")
            if message is f"Delete qubit {edge}":
                qubit = self.node.qmemory.get_matching_qubits('name', f'qsource-{edge}')
                logger.debug("Node %s deleting qubit %s",self.node.name, qubit)
                self.node.qmemory.remove(qubit)



class BipartiteOutputProtocol(NodeProtocol):
    """Defines behaviour of node when outputting qubits"""

    def __init__(self, node: Node, name: Optional[str] = None):
        super().__init__(node=node, name=name)

        mem_positions = self.node.qmemory.num_positions
        mem_ports = self.node.qmemory.ports
        self.q_out_ports = [value for key, value in self.node.ports.items() if "qout" in key]

        self.source_mem = [mem_ports[f"qin{num}"] for num in range(0, mem_positions, 2)]
        self.sources = [f"qsource-{port.name.lstrip('qout-')}" for port in self.q_out_ports]

    def _trigger_all_sources(self) -> None:
        """Trigger all sources on the node."""
        logger.debug("Triggering all sources.")
        
        for source in self.sources:
            # Trigger the source
            self.node.subcomponents[source].trigger()
            logger.debug(f"Triggered source {source}.")
        
    def _send_delete_instr(self) -> None:
        """Send a classical message to each reciever node."""
        logger.debug("Sending delete instructions to nodes.")
        for port_name, port in self.node.ports.items():
            if "cout" in port_name:
                edge = port_name.lstrip("cout-")
                port.tx_output(f"Delete qubit {edge}")

    def run(self) -> None:
        """The protocol to be run by a source node."""
        logger.debug(f"Running Output protocol.")

        await_all_sources = [
            self.await_port_input(port) for port in self.source_mem
        ]

        self._trigger_all_sources()
        while True:

            yield reduce(operator.and_, await_all_sources)
            logger.debug("Got all memory input from sources.")
            
            # Do entanglement
            logger.debug("Defining CreateGHZ program for obtained qubits.")
            bell_qubits = [pos for pos in self.node.qmemory.used_positions if pos % 2 == 0]
            prog = CreateGHZ(bell_qubits)

            logger.debug("Executing program.")
            self.node.subcomponents["qmemory"].execute_program(prog)

            # Wait for the program to finish
            yield self.await_program(self.node.qmemory)

            qubits = [self.node.qmemory.pop(pos)[0] for pos in self.node.qmemory.used_positions]
            fidelity_val = fidelity(qubits, gen_GHZ_ket(len(qubits)), squared=True)
            logger.debug(f"Fidelity: {fidelity_val}")
            logger.debug(f"Reduced dm of qubits: \n{reduced_dm(qubits)}")

            self.send_signal(Signals.SUCCESS, fidelity_val)

            self._send_delete_instr()
            
            #import pdb; pdb.set_trace()
