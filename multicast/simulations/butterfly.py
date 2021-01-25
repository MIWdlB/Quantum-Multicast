import netsquid as ns
from netsquid.components import Channel, QuantumChannel
from netsquid.nodes import nodes
import pydynaa
import numpy as np

from multicast.utils import Graph

ns.set_random_state(seed=123456789)

def buildButterfly(None) -> Graph:
    """Create a butterfly graph."""
    
    # We want 5 nodes
    nodes = {1,2,3,4,5}
    butterfly = Graph(nodes)
    
    butterfly.addEdge(start=0, end=1)
    butterfly.addEdge(start=0, end=2)
    butterfly.addEdge(start=1, end=2)
    butterfly.addEdge(start=2, end=3)
    butterfly.addEdge(start=2, end=4)
    butterfly.addEdge(start=3, end=4)

    butterfly.showEdges()



