import netsquid as ns
from netsquid.nodes import Network
from netsquid.util.simlog import get_loggers


from qmulticast.protocols import BipartiteProtocol, MultipartiteProtocol
from qmulticast.utils import create_bipartite_network , create_multipartite_network
from qmulticast.utils import multipartite_qubits, gen_GHZ_ket
import netsquid.qubits.qubitapi as qapi
from qmulticast.utils.graphlibrary import *

ns.set_random_state(seed=1234567)

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
    shandler.setLevel(logging.WARNING)
    shandler.setFormatter(formatter)
    simlogger.addHandler(shandler)


def simulate_network(network: Network, bipartite = True, source_val = "2" ) -> None:
    """Assign protocols and run simulation.

    Parameters
    ----------
    network : Network
        The network object to run simulation on.
    """
    protocols = []
    if(bipartite):
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


if __name__ == "__main__":
    run_bipartite = False
    source_node = "2"
    init_logs()
    logger.debug("Starting program.")
    graph = ButterflyGraph()
    logger.debug("Created graph.")
    if (run_bipartite):
        network = create_bipartite_network("bipartite-butterfly", graph)
    else:
        network = create_multipartite_network("bipartite-butterfly", graph)
    logger.debug("Created Network.")
    simulate_network(network,run_bipartite,source_node)
    qubits = multipartite_qubits(network)
    print("fidelity :"+str(qapi.fidelity(qubits, gen_GHZ_ket(len(qubits)), squared=True)))