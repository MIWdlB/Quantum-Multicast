"""Defines a general graph."""

from functools import abc
from pprint import pprint as print
from typing import Hashable

class Graph():
    """Graph class.
    
    """

    def __init__(self, nodes: list[Hashable] = None):
        """Intialise.
        
        Parameters
        ----------
        nodes : list[Hashable], default None
            A list of names or numbers for nodes.
        """
        self._nodes = set("" if nodes is None else nodes)
        self._edges = {}
        pass

    def addNode(self, node: Hashable) -> None:
        """Add a node to the graph."""

        if node in self._nodes:
            raise ValueError("A node with the name %s already exists.", node)

        self._nodes.add(node)
        self._edges[node] = {}

    def addNodes(self, nodes: list[Hashable]) -> None:
        """Add multiple nodes."""

        for node in nodes:
            self.addNode(node)

    def addEdge(self, start: Hashable, end: Hashable, weight: float = 1, directed: bool = False) -> None:
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

        if not (start in self._nodes and end in self._nodes):
            raise ValueError("You provided a node which does not exist.")
        
        self._edges[start][end] = weight

        if not directed:
            self._edges[end][start] = weight

    def showEdges(self) -> None:
        """Print out the edges.
        
        #TODO maybe make this a graph
        """
        print(self._edges)

