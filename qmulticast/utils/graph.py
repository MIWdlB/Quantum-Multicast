"""Defines a general graph."""

import logging
from pprint import pprint
from typing import Hashable, Set, List

logger = logging.getLogger(__name__)

class Graph:
    """Graph class."""

    def __init__(self, nodes: Set[Hashable] = None):
        """Intialise.

        Parameters
        ----------
        nodes : list[Hashable], default None
            A list of names or numbers for nodes.
        """
        logger.debug("Initialising graph.")
        self.nodes = set()
        self.edges = {}
        self.addNodes(nodes)

    def addNode(self, node: Hashable) -> None:
        """Add a node to the graph."""
        logger.debug(f"Adding node: {node}")
        if node in self.nodes:
            logger.error("Node name %s already exists", node)
            raise ValueError("A node with the name %s already exists.", node)

        self.nodes.add(node)
        self.edges[node] = {}

    def addNodes(self, nodes: List[Hashable]) -> None:
        """Add multiple nodes."""
        for node in nodes:
            self.addNode(node)

    def addEdge(
        self, start: Hashable, end: Hashable, weight: float = 1, directed: bool = False
    ) -> None:
        """Add an adge between two nodes.

        Parameters
        ----------
        start : Hashable
            the name or number of the node to start the edge from
        end : str
            the name or number of the node to end the edge on
        weight : float, default = 1
            the weight of the edge
        directed : bool, defualt = False
            Mark the edge as one directional.
        """
        prefix = 'un' if directed == False else ''
        logger.debug(f"Adding {prefix}directed edge:")
        logger.debug(f"\t{start} to {end} with weight: {weight}.")
        if not (start in self.nodes and end in self.nodes):
            raise ValueError("You provided a node which does not exist.")

        self.edges[start][end] = weight

        if not directed:
            self.edges[end][start] = weight

    def showEdges(self) -> None:
        """Print out the edges.

        #TODO maybe make this a graph
        """
        logger.debug("Printing edges to console.")
        pprint(self.edges)
        print()
