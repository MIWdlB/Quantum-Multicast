import networkx as nx
import matplotlib.pyplot as plt

#Two Connected Nodes
TwoNodes=nx.DiGraph()
TwoNodes.add_edge_from(1,2,1)

#Triangle Graph
TriangleGraph = nx.DiGraph()
TriangleGraphEdges = [(1, 2, 1), (1, 3, 1), (2, 3, 1)]
TriangleGraph.add_weighted_edges_from(TriangleGraphEdges)

#Butterfly Graph
ButterflyGraph = nx.DiGraph()
ButterflyGraphEdges = [(1, 2, 1), (1, 3, 1), (1, 4, 1), (1, 5, 1), (2, 3, 1), (4, 5, 1)]
ButterflyGraph.add_weighted_edges_from(ButterflyGraphEdges)

# Plot a graph
plt.plot()
nx.draw(ButterflyGraph)
plt.show()

#Repeater
Repeater = nx.DiGraph()
RepeaterEdges = [(1, 2, 1), (1, 3, 1)]
Repeater.add_edges_from(RepeaterEdges)
