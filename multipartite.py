import netsquid as ns
from netsquid.nodes import Network

from qmulticast.protocols import MultipartiteProtocol
from qmulticast.utils import create_multipartite_network
from qmulticast.utils.graphlibrary import *
import netsquid.qubits.qubitapi as qapi
from qmulticast.utils import gen_GHZ_ket,multipartite_qubits
import numpy as np
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

    global logger
    logger = logging.getLogger(__name__)


def simulate_network(network: Network,n_source = "0") -> []:
    """Assign protocols and run simulation.

    Parameters
    ----------
    network : Network
        The network object to run simulation on.
    """
    protocols = []
    for node in network.nodes.values():
        logger.debug("Adding protocol to node %s", node.name)
        if node.name == n_source:
            protocols.append(MultipartiteProtocol(node, source=True))
        else:
            protocols.append(MultipartiteProtocol(node, source=False))

    for protocol in protocols:
        protocol.start()

    logger.debug("Running sim.")
    ns.sim_run()
    results = [] # TODO
    return results


if __name__ == "__main__":
    init_logs()
    logger.debug("Starting program Multipartite.")
    graph = ButterflyGraph()
    source = "2"
    logger.debug("Created graph.")
    network = create_multipartite_network("bipartite-butterfly", graph)
    logger.debug("Created Network.")
    results = simulate_network(network,source)
    logger.debug("Simulation Finished")
    qubits = multipartite_qubits(network)
    print("fidelity to ghz:"+str(qapi.fidelity(qubits, gen_GHZ_ket(len(qubits)), squared=True)))

