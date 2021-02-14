"""Defines the protocol for an input node."""
import logging
import operator
from functools import reduce
from typing import List, Optional

from netsquid.components.component import Port
from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol

logger = logging.getLogger(__name__)


class QuantumInputProtocol(NodeProtocol):
    """ Defines behviour needed when a source expects input qubits."""

    def __init__(self, node: Node, name: Optional[str] = None) -> None:
        """Initialise
        
        Paramters
        ---------
        node : Node
            The node on which the protocol should be run.
        name : str
            A name to assign the protocol.
        """
        super().__init__(node=node, name=name)
        mem_positions = self.node.qmemory.num_positions
        mem_ports = self.node.qmemory.ports
        self.q_in_ports = [mem_ports[f"qin{num}"] for num in range(1, mem_positions, 2)]

        self.c_in_ports = [
            port for port in self.node.ports.values() if "cin" in port.name
        ]
        self.add_signal(label="recieved")

    def run(self) -> None:
        """Protocol for reciver."""
        # Get input
        logger.debug(f"Running Quantum Input protocol.")
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
