"""Defines the butterfly graph"""
import logging
import networkx as nx

logger = logging.getLogger(__name__)


class ButterflyGraph(nx.DiGraph):
    """Defines the butterfly graph."""

    def __init__(self):
        logger.debug("Creating butterfly graph")
        super().__init__()
        edges = {
            5: {1: 1, 2: 1},
            1: {5: 1, 2: 1},
            2: {5: 1, 1: 1, 3: 1, 4: 1},
            3: {2: 1, 4: 1},
            4: {2: 1, 3: 1},
        }
        temp = nx.DiGraph(edges)
        self.add_edges_from(temp.edges)


class TwinGraph(nx.DiGraph):
    """Two nodes connected."""

    def __init__(self):
        super().__init__()
        logger.debug("Creating twin graph.")
        edges = {0: {1: 1}, 1: {0: 1}}
        temp = nx.DiGraph(edges)
        self.add_edges_from(temp.edges)

class RepeaterGraph(nx.DiGraph):
    """Single repeater."""

    def __init__(self):
        super().__init__()
        logger.debug("Creating repeater graph.")
        edges = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1}}
        temp = nx.DiGraph(edges)
        self.add_edges_from(temp.edges)

class TriangleGraph(nx.DiGraph):
    """Three fully connected nodes."""

    def __init__(self):
        super().__init__()
        logger.debug("Creating triangle graph.")
        edges = {0: {1: 1, 2: 1}, 1: {0: 1, 2: 1}, 2: {0: 1, 1: 1}}
        temp = nx.DiGraph(edges)
        self.add_edges_from(temp.edges)
