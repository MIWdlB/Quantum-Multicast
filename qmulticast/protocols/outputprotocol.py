"""Defines the base output protocol."""

import logging
from typing import Optional

from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol

from qmulticast.utils import fidelity_from_node

logger = logging.getLogger(__name__)


class OutputProtocol(NodeProtocol):
    """Defines behaviour of node when outputting qubits"""

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
        """Wait for a qubit to be received at the end of a channel.
        
        Paramters
        ---------
        port_name : str
            The name of an ns.Port object to find the transmission time of.
        """

        connection = self.node.ports[port_name].connected_port.component
        channel = connection.channel_AtoB

        delay = channel.compute_delay()
        logger.debug(f"Found transmission time {delay} for channel {channel.name}")

        # Have to wait slightly longer than transmission time as NS
        # doesn't let us have access to things at the instant they happen.
        return delay * 1.0000001

    def run(self) -> None:
        """The main run function should be defined in subclasses."""
        pass
