"""Defines a general graph."""

import logging
from pprint import pprint
from typing import Dict, Hashable, List, Set

logger = logging.getLogger(__name__)


class Graph:
    """Graph class.

    Properties
    ----------
    nodes : Set[Hashable]
        Nodes with unique names.
    edges : Dict[Hashble, Dict[Hashable, float]
        Directed weighted edges starting at each node.
    """

    def __init__(self, nodes: Set[Hashable] = None) -> None:
        """Intialise.

        Parameters
        ----------
        nodes : set[Hashable], default None
            A set of names or numbers for nodes.
        """
        logger.debug("Initialising graph.")
        self.nodes: Set(str) = set()
        self.edges: Dict[Hashable, Dict[Hashable, float]] = {}
        self.addNodes({node for node in nodes})

    def addNode(self, node: Hashable) -> None:
        """Add a node to the graph.

        Parameters
        ----------
        node : Hashable
            A node identifier.
        """
        logger.debug(f"Adding node: {node}")
        if node in self.nodes:
            logger.error("Node name %s already exists", node)
            raise ValueError("A node with the name %s already exists.", node)

        self.nodes.add(node)
        self.edges[node] = {}

    def addNodes(self, nodes: Set[Hashable]) -> None:
        """Add multiple nodes.

        Parameters
        ----------
        nodes : Set[Hashable]
            A set of nodes to add.
        """
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
        end : Hashable
            the name or number of the node to end the edge on
        weight : float, default = 1
            the weight of the edge
        directed : bool, default = False
            Mark the edge as one directional.
        """
        prefix = "un" if directed == False else ""
        logger.debug(f"Adding {prefix}directed edge:")
        logger.debug(f"\t{start} to {end} with weight: {weight}.")
        if not (start in self.nodes and end in self.nodes):
            raise ValueError("You provided a node which does not exist.")

        self.edges[start][end] = weight

        if not directed:
            self.edges[end][start] = weight

    def showEdges(self) -> None:
        """Print out the edges.

        #TODO make this a graph
        """
        logger.debug("Printing edges to console.")
        pprint(self.edges)
        print()
