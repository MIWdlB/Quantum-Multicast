"""Defines the protocol to be followed at a node bipartite source(s)"""
import logging
import operator
from functools import reduce
from typing import Optional

from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol
from netsquid.protocols.protocol import Signals
from netsquid.qubits.qubitapi import fidelity, reduced_dm

from qmulticast.utils import fidelity_from_node, gen_GHZ_ket
from qmulticast.programs import CreateGHZ
from qmulticast.utils.functions import log_entanglement_rate
from .bipartiteprotocol import BipartiteInputProtocol
logger = logging.getLogger(__name__)

handler = logging.FileHandler(filename="fidelity-data.txt", mode="w")

res_logger = logging.Logger(name="results")
res_logger.addHandler(handler)


class MultipartiteProtocol(NodeProtocol):
    """Class defining the protocol of a bipartite network node.

    If the node is a source, send out entangled qubits.
    If the node is a reciever, await incoming qubit and classical message.
    TODO (if we make larger networks) If node recives a qubit not for itself, forward that message onwards
    If node has recived its required qubit, return a (classical) flag to source to say its happy
    """

    def __init__(
        self,
        node: Node,
        name: Optional[str] = None,
        source: bool = False,
        receiver: bool = True,
        routing_table = None):
        """
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

        self.input_ports = [port for port in self.node.qmemory.ports if "qin" in port]
        self.input_ports.remove("qin")
        self.input_ports = [
            port for port in self.input_ports if int(port.lstrip("qin")) % 2 == 1
        ]
        self.fidelity = fidelity_from_node(self.node)

        self._output = source
        self._input = receiver

        if self._output:
            self.add_subprotocol(MultipartiteOutputProtocol(self.node))

        if self._input:
            self.add_subprotocol(BipartiteInputProtocol(self.node))

    def run(self):
        """Run the protocol."""
        node = self.node
        logger.debug(f"Running bipartite protocol on node {node.name}.")
        self.start_subprotocols()

class MultipartiteOutputProtocol(NodeProtocol):
    """ Defines behviour needed when a source expects input qubits."""

    def __init__(self, node: Node, name: Optional[str] = None):
        super().__init__(node=node, name=name)
        self._mem_size = self.node.qmemory.num_positions
        mem_positions = self.node.qmemory.num_positions
        mem_ports = self.node.qmemory.ports
        self.q_in_ports = [mem_ports[f"qin{num}"] for num in range(1, mem_positions, 2)]

        self.c_in_ports = [
            port for port in self.node.ports.values() if "cin" in port.name
        ]

    def run(self):
        """Protocol for reciver."""
        # Get input
        logger.debug(f"Running Multi output protocol.")

        self.start_subprotocols()
        """Run the protocol."""
        node = self.node
        logger.debug(f"Running multipartite protocol on node {node.name}.")
        logger.debug(f"Node: {node.name} " + f"has {self._mem_size} memory slots.")
        counter = 0
        has_triggered = False
        while (counter < 1): #looping issue?
            counter += 1
            self.node.subcomponents[f"qsource-{node.name}"].trigger()
            logger.debug(f"Triggered source qsource-{node.name}.")
            has_triggered = True

            yield self.await_port_input(node.qmemory.ports["qin0"])

            logger.debug("source got own qubit in memory")

            self.send_signal(Signals.SUCCESS) # unused


    # def run(self):
    #     """Run the protocol."""
    #     node = self.node
    #     logger.debug(f"Running multipartite protocol on node {node.name}.")
    #     logger.debug(f"Node: {node.name} " + f"has {self._mem_size} memory slots.")
    #     counter = 0
    #     has_triggered = False
    #     while (counter < 1): #looping issue?
    #         # Send from source.
    #         # - out to all connection ports.
    #         counter += 1
    #         if self._is_source and has_triggered==False: 

    #             # generate GHZ state
    #             # keep qubit 0, send rest out
    #             self.node.subcomponents[f"qsource-{node.name}"].trigger()
    #             logger.debug(f"Triggered source qsource-{node.name}.")
    #             has_triggered = True

    #             yield self.await_port_input(node.qmemory.ports["qin0"])

    #             logger.debug("source got own qubit in memory")

    #             self.send_signal(Signals.SUCCESS) # unused

    #         if not self._is_source:
    #             # Get input
    #             await_any_input = [
    #                 self.await_port_input(self.node.qmemory.ports[port])
    #                 for port in self.input_ports
    #             ]
    #             # not awaiting properly

    #             yield reduce(operator.or_, await_any_input)

    #             #  TODO recive input, forward onto required place
                
    #             logger.debug(
    #                 f"Got input: memory useage node: {self.node.name}: {self.node.qmemory.used_positions}"
    #             )
    #             self.send_signal(Signals.SUCCESS) # unused
    #         #next(self.fidelity)
