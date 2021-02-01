import netsquid as ns
from netsquid.nodes import Network

from qmulticast.protocols import MultipartiteProtocol
from qmulticast.utils import create_multipartite_network
from qmulticast.utils.graphlibrary import *
import netsquid.qubits.qubitapi as qapi
from qmulticast.utils import gen_GHZ_ket
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


def simulate_network(network: Network) -> []:
    """Assign protocols and run simulation.

    Parameters
    ----------
    network : Network
        The network object to run simulation on.
    """
    network_source = "1" # source of GHZ state
    protocols = []
    for node in network.nodes.values():
        logger.debug("Adding protocol to node %s", node.name)
        if node.name == network_source:
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
    graph = TriangleGraph()
    logger.debug("Created graph.")
    network = create_multipartite_network("bipartite-butterfly", graph)
    logger.debug("Created Network.")
    results = simulate_network(network)
    logger.debug("Simulation Finished")
    import pdb; pdb.set_trace()
    q1 = network.nodes['0'].qmemory.peek(1)[0]#.qstate.qrepr.reduced_dm())
    q2 = network.nodes['1'].qmemory.peek(1)[0]#.qstate.qrepr.reduced_dm())
    q2 = network.nodes['2'].qmemory.peek(1)[0]#.qstate.qrepr.reduced_dm())
    qapi.combine_qubits([q1, q2])
    print(print(qapi.reduced_dm([q1,q2])))
    print(qapi.fidelity([q1,q2], gen_GHZ_ket(2), squared=True))
    print("all done")
