import networkx as nx
from networkx.algorithms import approximation as ax
import numpy as np
import matplotlib.pyplot as plt
from qmulticast.utils import ButterflyGraph, Graph, TwinGraph


def get_edges(graph):
    edges = []
    for key, value in graph.edges.items():
        node_A =  key 
        for key, value in value.items(): 
            node_B =  key 
            edges.append((node_A,node_B))
    return edges

def draw_graph(graph):
    G = nx.Graph()
    edges = get_edges(graph)
    G.add_edges_from(edges)
    plt.figure()
    nx.draw(G)
    plt.show()

def draw_steiner_tree(graph):
    G = nx.Graph()
    edges = get_edges(graph)
    G.add_edges_from(edges)
    points = list(G.nodes)
    graph2 = ax.steinertree.steiner_tree(G, points)
    plt.figure()
    nx.draw_networkx(graph2)
    print(graph2.nodes)
    plt.show()


if __name__ == "__main__":
    graph = ButterflyGraph()
    #graph = TwinGraph()
    draw_graph(graph)
    draw_steiner_tree(graph)
   