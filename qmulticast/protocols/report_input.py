"""Protocol to look at a single port and report when it gets input.

NOT IN USE
"""

import logging

from netsquid.components.component import Port
from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol

logger = logging.getLogger(__name__)


class MoveInput(NodeProtocol):
    """Class to watch for any change to the memory."""

    def __init__(self, node: Node, mem_port: Port) -> None:
        """Initialise
        
        Paramters
        ---------
        node : Node
            The node on which the protocol should be run.
        name : str
            A name to assign the protocol.
        """
        super().__init__()
        self.node = node
        self.port = mem_port
        self.mem_pos = int(mem_port.name.lstrip("qin"))
        self.qmemory = node.qmemory

    def run(self) -> None:
        """Main protocol."""
        # Get input
        # - from all ports
        # - they all go to their own memory slot
        while True:
            yield self.await_port_input(self.port)
            logger.debug("Got input to port %s", self.port)
            measurement = self.qmemory.measure(positions=self.mem_pos)
            print(measurement)

        # Do an entangling operation
        # - find which pairwise operations to do?

        # signal success to the superprotocol

    def move_input_qubit(self) -> None:
        """Move the qubit on the input location to a free space."""
        spaces = self.node.qmemory.unused_positions
        if spaces:
            input_qubit = self.node.qmemory.pop(self.mem_pos)
            logger.debug(f"Node {self.node.name} got qubit {input_qubit}")
            self.node.qmemory.put(qubits=input_qubit, positions=spaces[0])
            logger.debug("\tput qubit in memory position %s", spaces[0])
            logger.debug(f"\tEmpty memory: {self.node.qmemory.unused_positions}")
        else:
            logger.debug(f"Node: {self.node.name} No memory spaces left.")
