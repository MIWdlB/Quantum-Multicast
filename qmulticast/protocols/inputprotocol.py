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
                # Protocols must have diffrent names to run in parralel!
                logger.debug("Adding repeater protocol for port %s", port.name)
                self.add_subprotocol(RepeaterProtocol(self.node, port, name=f"repeater-{port.name}"))
        else:
            # if not a repeater just forward on the ports.
            logger.debug(f"Forawrding input for node {self.node.name}.")
            mem_position = 1
            for port in node.ports.values():
                if "out" in port.name:
                    continue
                if "cin" in port.name:
                    continue

                logger.debug("Redirecting input port to memory %s.", mem_position)

                # Now from the connection we need to redirect the qubit to the
                # qmemory of the recieving node.
                # TODO how do we assing it to an empyty memory slot.

                port.forward_input(
                    node.subcomponents["qmemory"].ports[f"qin{mem_position}"]
                )
                mem_position += 2

    def run(self):
        """Protocol for reciver."""
        # Get input
        logger.debug(f"Running Input protocol on node {self.node.name}")

        self.start_subprotocols()

        while True:
            await_quantum_input = [self.await_port_input(port) for port in self.q_mem_ports]
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
        logger.debug(f"Initilaising repeater proocol on node {node.name}")
        self.node = node
        self.port = port
        
        self.routes = self.node.routing_table
        logger.debug(f"Got routing table {self.routes}")

        mem_positions = self.node.qmemory.num_positions
        mem_ports = self.node.qmemory.ports
        self.q_mem_ports = [mem_ports[f"qin{num}"] for num in range(1, mem_positions, 2)]

        self.c_in_ports = [
            port for port in self.node.ports.values() if "cin" in port.name
        ]

        self.q_in_ports = [
            port for port in self.node.ports.values() if "qin" in port.name
        ]

    def run(self) -> None:
        """Main protocol."""
        # need to disconnect port from going straight to memory
        # so that we can forward qubits first

        logger.debug(f"Ready to forward on port {self.port.name}")

        _, sender, here = self.port.name.split("-")

        sender_destinations = [
            dest for dest, forward in self.routes[int(sender)].items() 
            if forward == int(here)
        ]

        forward_nodes = [self.routes[int(here)][dest] for dest in sender_destinations]
        
        logger.debug(f"\tto nodes {sender_destinations} via {forward_nodes}")

        while True:
            yield self.await_port_input(self.port)
            logger.debug(f"Got message into port {self.port}")
            message = self.port.rx_input()
            #import pdb; pdb.set_trace()
            origin = message.meta["origin"]
            dest = message.meta["dest"]

            if dest == here:
                pos = [pos for pos in self.node.qmemory.unused_positions 
                if pos % 2 == 1][0]
                self.node.qmemory.put(message.items, positions=pos)
            else:
                forward_node = self.routes[int(here)][int(dest)]
                self.node.ports[f"qout-{here}-{forward_node}"].tx_output(message)
                logger.debug(f"Forwarded qubit from {origin} to {dest} via {forward_node}.")

