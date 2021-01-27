"""Defines the protocol to be followed at a node bipartite source(s)"""

import logging
from netsquid.protocols import NodeProtocol
from netsquid.nodes import Node
from netsquid.components.instructions import INSTR_EMIT

logger = logging.getLogger(__name__)


class BipartiteProtocol(NodeProtocol):
    """Class defining the protocol of a bipartite network node.

    First draft I'll assum it's the twin graph
    """

    def __init__(self, node: Node, name=None, source: bool = False):
        """Initialise the protocol wiht information about the node."""
        logger.debug("Initialising Bipartite protocol.")
        super().__init__(node=node, name=name)
        self.input_ports = [
            port for port in self.node.ports.values() if "in" in port.name
        ]
        self.output_ports = [
            port for port in self.node.ports.values() if "out" in port.name
        ]
        # TODO make this general for N connections
        self._is_source = source

        self._mem_size = self.node.qmemory.num_positions - 1
        self._mem_input_port = self.node.qmemory.ports[f"qin{self._mem_size}"]

    def run(self):
        """Run the protocol."""
        node = self.node
        logger.debug(f"Running bipartite protocol on node {node.name}.")
        counter = 0
        while counter < 1:
            # Send from source.
            # - out to all connection ports.
            counter += 1
            if self._is_source:
                for port in self.output_ports:
                    logger.debug(f"Found port {port.name}")
                    edge = port.name.lstrip("out-")

                    # Trigger the source
                    source_name = "qsource-" + edge

                    # May need a subprototocol here to see if we can
                    # add wait conditions for multiple inputs
                    # do subprotocols work in parrallel?

                    self.node.subcomponents[source_name].trigger()
                    logger.debug("Triggered source.")
                    # import pdb;pdb.set_trace()

            # Await input.seems to be a method of the NodeProtocol
            # TODO this assumes we have one for now.

            unused_mem = self.node.qmemory.unused_positions
            logger.debug(f"Node {self.node.name} waiting for input.")

            # for each connection we need a subprotocol.

            yield self.await_port_input(self._mem_input_port)
            input_qubit = self.node.qmemory.peek(self._mem_size)
            logger.debug(f"Got qubit {input_qubit}")

        # - move input to available qmemory slot.

        # Entangle swap.
        # - entangle swap with node to ensure that
