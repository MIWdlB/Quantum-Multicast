from networkx.drawing.nx_pylab import draw_networkx
from qmulticast.utils.graphlibrary import ButterflyGraph
import matplotlib.pyplot as plt

if __name__ == "__main__":
    graph = ButterflyGraph()
    draw_networkx(graph)
   # Set margins for the axes so that nodes aren't clipped
    ax = plt.gca()
    ax.margins(0.20)
    plt.axis("off")
    plt.savefig(fname="graphplot")