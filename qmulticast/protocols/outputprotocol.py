"""Defines the base output protocol."""

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
from .inputprotocol import QuantumInputProtocol

logger = logging.getLogger(__name__)

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
            self.add_subprotocol(OutputProtocol(self.node))

        if self._input:
            self.add_subprotocol(QuantumInputProtocol(self.node, name=f"input-{self.node.name}"))

    def run(self):
        """Run the protocol."""
        node = self.node
        logger.debug(f"Running bipartite protocol on node {node.name}.")
        self.start_subprotocols()


class OutputProtocol(NodeProtocol):
    """Defines behaviour of node when outputting qubits"""

    def __init__(self, node: Node, name: Optional[str] = None):
        super().__init__(node=node, name=name)
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