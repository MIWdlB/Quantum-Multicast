"""Defines the input protocol for both multipartite and bipartite."""
import logging
import operator
from functools import reduce
from typing import List, Optional

from netsquid.components.component import Port
from netsquid.components.instructions import INSTR_X
from netsquid.components.qprogram import QuantumProgram
from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol

logger = logging.getLogger(__name__)

class InputProtocol(NodeProtocol):
    """ Defines behviour needed when a source expects input qubits."""

    def __init__(self, node: Node, name: Optional[str] = None, repeater: bool = False) -> None:
        super().__init__(node=node, name=name)

        mem_positions = self.node.qmemory.num_positions
        mem_ports = self.node.qmemory.ports
        self.q_mem_ports = [mem_ports[f"qin{num}"] for num in range(1, mem_positions, 2)]

        self.c_in_ports = [
            port for port in self.node.ports.values() if "cin" in port.name
        ]

        self.q_in_ports = [
            port for port in self.node.ports.values() if "qin" in port.name
        ]

        if repeater:
            for port in self.q_in_ports:
                self.add_subprotocol(RepeaterProtocol(self.node, port))


    def run(self):
        """Protocol for reciver."""
        # Get input
        logger.debug(f"Running Input protocol on node {self.node.name}")
        await_quantum_input = [self.await_port_input(port) for port in self.q_mem_ports]

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


class RepeaterProtocol(NodeProtocol):
    """Forward input to port."""
    def __init__(self, node: Node, port: Port, name: Optional[str] = None) -> None:
        super().__init__(node=node, name=name)
        self.port = port
        try: 
            self.routes = self.node.routing_table[node.name]
        except KeyError:
            self.routes = self.node.routing_table[int(node.name)]
        
    def run(self) -> None:
        """Main protocol."""
        # need to disconnect port from going straight to memory
        # so that we can forward qubits first
        import pdb; pdb.set_trace()
        logger.debug(f"Ready to forward on port {self.port.name}")
        while True:
            yield self.await_port_input(self.port)
            logger.debug(f"Got message into port {self.port}")
            message = self.port.rx_input()
            import pdb;pdb.set_trace()

            qubits = [] # TODO get the qubits from message
            for qubit in qubits:
                ...