import netsquid as ns
from netsquid.nodes import Network

from qmulticast.protocols import BipartiteProtocol
from qmulticast.utils import create_bipartite_network
from qmulticast.utils.graphlibrary import *

ns.set_random_state(seed=1234567)

import logging


def init_logs() -> None:
    """Set up logging.

    TODO this properly with handlers and formatters so that
    we can get results out in their own file.
    """
    logging.basicConfig(
        filename="logs.log",
        filemode="w",
        format="%(asctime)s:%(levelname)s:%(filename)s - %(message)s",
        level=logging.DEBUG,
    )

    global logger
    logger = logging.getLogger(__name__)


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


if __name__ == "__main__":
    init_logs()
    logger.debug("Starting program.")
    graph = TriangleGraph()
    logger.debug("Created graph.")
    network = create_bipartite_network("bipartite-butterfly", graph)
    logger.debug("Created Network.")
    network = simulate_network(network)
