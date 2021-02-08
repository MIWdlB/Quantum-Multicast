"""Defines the base output protocol."""

import logging
import operator
from functools import reduce
from typing import List, Optional

from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol
from qmulticast.utils import fidelity_from_node
logger = logging.getLogger(__name__)

class OutputProtocol(NodeProtocol):
    """Defines behaviour of node when outputting qubits"""

    def __init__(self, node: Node, name: Optional[str] = None):
        super().__init__(node=node, name=name)
        logger.debug("Initialing base output protocol.")
        self.fidelity = fidelity_from_node(self.node)

    def _send_all_delete(self) -> None:
        """Send a classical message to each reciever node."""
        logger.debug("Sending delete instruction to all nodes.")
        for port_name, port in self.node.ports.items():
            if "cout" in port_name:
                edge = port_name.lstrip("cout-")
                port.tx_output(f"Delete qubit {edge}")

    def _transmission_time(self, port_name: str) -> None:
        """Wait for a qubit to be received at the end of a channel."""

        connection = self.node.ports[port_name].connected_port.component
        channel = connection.channel_AtoB

        delay = channel.compute_delay()
        logger.debug(f"Found transmission time {delay} for channel {channel.name}")

        return delay * 1.0000001

    def run(self) -> None:
        """The main run function should be defined in subclasses."""
        pass