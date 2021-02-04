import netsquid as ns
from netsquid.nodes import Network
from netsquid.util.simlog import get_loggers

from qmulticast.protocols import BipartiteProtocol
from qmulticast.utils import create_bipartite_network
from qmulticast.utils.graphlibrary import *
import numpy as np

ns.set_random_state(seed=123456)

import logging


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

    simlogger = logging.getLogger("netsquid")
    simlogger.setLevel(logging.DEBUG)
    fhandler = logging.FileHandler("simlogs.txt", mode="w")
    fhandler.setFormatter(formatter)
    simlogger.addHandler(fhandler)

    shandler = logging.StreamHandler()
    shandler.setLevel(logging.ERROR)
    shandler.setFormatter(formatter)
    simlogger.addHandler(shandler)


def simulate_network(network: Network) -> None:
    """Assign protocols and run simulation.

    Parameters
    ----------
    network : Network
        The network object to run simulation on.
    """
    protocols = []
    for node in network.nodes.values():
        logger.debug("Adding protocol to node %s", node.name)
        if node.name == "2":
            protocols.append(BipartiteProtocol(node, source=True))
        else:
            protocols.append(BipartiteProtocol(node, source=False))

    for protocol in protocols:
        protocol.start()

    logger.debug("Running sim.")
    ns.sim_run()
    ns.sim_reset()


if __name__ == "__main__":
    with open("statistics.txt", mode="w") as file:
        pass
    logger.debug("Starting program.")
    for length in np.linspace(0, 500, 10):
        init_logs()
        graph = ButterflyGraph(length=length)
        logger.debug("Created graph.")
        network = create_bipartite_network("bipartite-butterfly", graph)
        logger.debug("Created Network.")
        network = simulate_network(network)
