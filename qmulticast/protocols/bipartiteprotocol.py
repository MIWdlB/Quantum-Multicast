"""Defines the protocol to be followed at a node bipartite source(s)"""

import logging
from netsquid.protocols import NodeProtocol

logger = logging.getLogger(__name__)

class BipartiteProtocol(NodeProtocol):
    """Class defining the protocol of a bipartite network node.
    
    """
    def __init__():
        """Initialise the protocol wiht information about the node."""
        pass


    def run(self):
        """Run the protocol."""
        node = self.node
        logger.debug(f"Running bipartite protocol on node {node.name}.")

        # Send from source.
        # - out to all connection ports.

        # Await input.
        # - move input to available qmemory slot

        # Entangle swap.
        # - entangle swap with node to ensure that