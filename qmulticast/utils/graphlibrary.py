"""Defines the butterfly graph"""
import logging

from qmulticast.utils.graph import Graph

logger = logging.getLogger(__name__)


class ButterflyGraph(Graph):
    """Defines the butterfly graph."""

    def __init__(self):
        logger.debug("Creating butterfly graph")
        self.nodes = {0, 1, 2, 3, 4}
        self.edges = {
            0: {1: 1, 2: 1},
            1: {0: 1, 2: 1},
            2: {0: 1, 1: 1, 3: 1, 4: 1},
            3: {2: 1, 4: 1},
            4: {2: 1, 3: 1},
        }


class TwinGraph(Graph):
    """Two nodes connected."""

    def __init__(self):
        logger.debug("Creating twin graph.")
        self.nodes = {0, 1}
        self.edges = {0: {1: 1}, 1: {0: 1}}


class RepeaterGraph(Graph):
    """Single repeater."""

    def __init__(self):
        logger.debug("Creating repeater graph.")
        self.nodes = {0, 1, 2}
        self.edges = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1}}
