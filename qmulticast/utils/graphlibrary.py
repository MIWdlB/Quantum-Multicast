"""Defines the butterfly graph"""
import logging
import networkx as nx

logger = logging.getLogger(__name__)


class ButterflyGraph(nx.DiGraph):
    """Defines the butterfly graph."""

    def __init__(self, length: float = 1):
        logger.debug("Creating butterfly graph")
        super().__init__()
        edges = {
            0: {1: length, 2: length},
            1: {0: length, 2: length},
            2: {0: length, 1: length, 3: length, 4: length},
            3: {2: length, 4: length},
            4: {2: length, 3: length},
        }
        for start in edges:
            for end in edges[start]:
                self.add_edge(str(start), str(end), weight=edges[start][end])

        self.name = "Butterfly"
        self.length = length


class TwinGraph(nx.DiGraph):
    """Two nodes connected."""

    def __init__(self, length: float = 1):
        super().__init__()
        logger.debug("Creating twin graph.")
        edges = {0: {1: length}, 1: {0: length}}
        for start in edges:
            for end in edges[start]:
                self.add_edge(str(start), str(end), weight=edges[start][end])
        self.name = "Twin"
        self.length = length


class RepeaterGraph(nx.DiGraph):
    """Single repeater."""

    def __init__(self, length: float = 1):
        super().__init__()
        logger.debug("Creating repeater graph.")
        edges = {0: {1: length}, 1: {0: length, 2: length}, 2: {1: length}}
        for start in edges:
            for end in edges[start]:
                self.add_edge(str(start), str(end), weight=edges[start][end])
        self.name = "Repeater"
        self.length = length


class TriangleGraph(nx.DiGraph):
    """Three fully connected nodes."""

    def __init__(self, length: float = 1):
        super().__init__()
        logger.debug("Creating triangle graph.")
        edges = {0: {1: length, 2: length}, 1: {0: length, 2: length}, 2: {0: length, 1: length}}
        for start in edges:
            for end in edges[start]:
                self.add_edge(str(start), str(end), weight=edges[start][end])
        self.name = "Triangle"
        self.length = length
