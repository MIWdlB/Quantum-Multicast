import netsquid as ns
from netsquid.nodes import Network
from netsquid.util.simlog import get_loggers


from qmulticast.protocols import BipartiteProtocol, MultipartiteProtocol
from qmulticast.utils import create_bipartite_network , create_multipartite_network
from qmulticast.utils import gen_GHZ_ket
import netsquid.qubits.qubitapi as qapi
from qmulticast.utils.graphlibrary import *
import numpy as np

ns.set_random_state(seed=123456)

import logging
import sys


def init_logs() -> None:
    """Set up logging.

    TODO this properly with handlers and formatters so that
    we can get results out in their own file.
    """
    logging.basicConfig(
        filename="logs.txt",
        filemode="w",
        format="%(asctime)s:%(levelname)s:%(filename)s - %(message)s",
        level=logging.DEBUG,
    )

    formatter = logging.Formatter(
        "%(asctime)s:%(levelname)s:%(filename)s - %(message)s"
    )

    global logger
    logger = logging.getLogger(__name__)

    # simlogger = logging.getLogger("netsquid")
    # simlogger.setLevel(logging.DEBUG)
    # fhandler = logging.FileHandler("simlogs.txt", mode="w")
    # fhandler.setFormatter(formatter)
    # simlogger.addHandler(fhandler)

    # shandler = logging.StreamHandler(stream=sys.stdout)
    # shandler.setLevel(logging.ERROR)
    # shandler.setFormatter(formatter)
    # simlogger.addHandler(shandler)


def simulate_network(network: Network, bipartite = True, source_val = "2" ) -> None:
    """Assign protocols and run simulation.

    Parameters
    ----------
    network : Network
        The network object to run simulation on.
    """
    protocols = []
    if bipartite:
        for node in network.nodes.values():
            logger.debug("Adding protocol to node %s", node.name)
            if node.name == source_val:
                protocols.append(BipartiteProtocol(node, source=True,receiver = False))
            else:
                protocols.append(BipartiteProtocol(node))
    else:
        for node in network.nodes.values():
            logger.debug("Adding protocol to node %s", node.name)
            if node.name == source_val:
                protocols.append(MultipartiteProtocol(node, source=True, receiver = False))
            else:
                protocols.append(MultipartiteProtocol(node))

    for protocol in protocols:
        protocol.start()

    logger.debug("Running sim.")
    ns.sim_run()
    ns.sim_reset()


if __name__ == "__main__":
    min_length = 0
    max_length = 10
    steps = 100
    min_nodes = 5
    max_nodes = 5
    for num_nodes in range(min_nodes, max_nodes+1):
        output_file = f"data/statistics-len:{min_length}-{max_length}-nodes:{num_nodes}.csv"
        with open(output_file, mode="w") as file:
            file.writelines("number of edges, edge length, p_loss_length, p_loss_init\n")
            file.writelines("runs, mean fidelity, loss rate, min time, mean time, entanglement rate\n")

        logger.debug("Starting program.")
        for length in np.linspace(min_length, max_length, steps):
            print(f"Calculating with {num_nodes} nodes and length {length}")
            init_logs()
            graph = nx.DiGraph()
            graph.length = length
            for node in range(1, num_nodes+1):
                graph.add_edge(str(0), str(node), weight=length)
                graph.add_edge(str(node), str(0), weight=length)
            logger.debug("Created multipartite graph.")
            network = create_bipartite_network("bipartite-butterfly", graph, output_file)
            logger.debug("Created multipartite Network.")
            network = simulate_network(network)
            
            logger.debug("Created multipartite graph.")
            network = create_bipartite_network("bipartite-butterfly", graph, output_file)
            logger.debug("Created multipartite Network.")
            network = simulate_network(network)
        
