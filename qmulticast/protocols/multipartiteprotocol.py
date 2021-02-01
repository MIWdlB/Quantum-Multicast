"""Defines the protocol to be followed at a node bipartite source(s)"""
import logging
import operator
from functools import reduce
from typing import Optional

from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol
from netsquid.protocols.protocol import Signals
from netsquid.qubits.qubitapi import fidelity, reduced_dm

from qmulticast.programs import CreateGHZ
from qmulticast.utils import gen_GHZ_ket

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

    def __init__(self, node: Node, name: Optional[str] = None, source: bool = False, routing_table = None):
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

        self.input_ports = [port for port in self.node.qmemory.ports if "qin" in port]
        self.input_ports.remove("qin")
        self.input_ports = [
            port for port in self.input_ports if int(port.lstrip("qin")) % 2 == 1
        ]

        self.source_mem = [port for port in self.node.qmemory.ports if "qin" in port]

        self.source_mem.remove("qin")
        self.source_mem = [
            port for port in self.source_mem if int(port.lstrip("qin")) % 2 == 0
        ]

        self.output_ports = [
            port for port in self.node.ports.values() if "out" in port.name
        ]

        self._is_source = source
        self._mem_size = self.node.qmemory.num_positions

        # for port_num in range(self._mem_size):
        #     # We assume input memory ports are the odd numbers.
        #     if port_num % 2 == 1:
        #         logger.debug("Adding move protocol for port %s", port_num)
        #         self.add_subprotocol(
        #             MoveInput(self.node, node.qmemory.ports[f"qin{port_num}"])
        #         )

    def run(self):
        """Run the protocol."""
        node = self.node
        logger.debug(f"Running multipartite protocol on node {node.name}.")
        logger.debug(f"Node: {self.node.name} " + f"has {self._mem_size} memory slots.")

        while (counter := 0 < 1):
            # Send from source.
            # - out to all connection ports.
            counter += 1
            if self._is_source: 
                # generate GHZ state n+1
                # keep qubit 0, send rest out
                for port in self.output_ports:
                    logger.debug(f"Found port {port.name}")
                    edge = port.name.lstrip("out-")

                    # Trigger the source
                    source_name = "qsource-" + edge
                    self.node.subcomponents[source_name].trigger()
                    logger.debug(f"Triggered source {source_name}.")

                await_all_sources = [
                    self.await_port_input(self.node.qmemory.ports[port])
                    for port in self.source_mem
                ]
                yield reduce(operator.and_, await_all_sources)

                logger.debug("Got all memory input from sources.")
                # Do entanglement

                # fidelity_val = fidelity(qubits, gen_GHZ_ket(len(qubits)), squared=True)
                # logger.debug(f"Fidelity: {fidelity_val}")
                # logger.debug(f"Reduced dm of qubits: \n{reduced_dm(qubits)}")

                self.send_signal(Signals.SUCCESS)

            if not self._is_source:
                # Get input
                await_any_input = [
                    self.await_port_input(self.node.qmemory.ports[port])
                    for port in self.input_ports
                ]
                yield reduce(operator.or_, await_any_input)
                # recive input, forward onto required place
                
                logger.debug(
                    f"Got input: memory useage {self.node.qmemory.used_positions}"
                )
                logger.debug(
                    f"Node {self.node.name} used memory: {self.node.qmemory.used_positions}"
                )
                self.send_signal(Signals.FAIL, self.local_qcount)