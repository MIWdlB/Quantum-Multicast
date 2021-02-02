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
    # for j in range(5):
    #     print(j)
    #     for i in range(10):
    #         print(network.nodes[f"{j}"].qmemory.peek(i))
    #     print()

    # i'm sorry this is so ugly
    if (graph.name == "Butterfly graph"):
        qubits = []
        qubits.append( network.nodes['0'].qmemory.peek(3)[0]) # to do with the order that locations are assigned i think
        qubits.append( network.nodes['1'].qmemory.peek(3)[0]) # needs fixing
        qubits.append( network.nodes['2'].qmemory.peek(0)[0]) # source node qubit always in pos0
        qubits.append( network.nodes['3'].qmemory.peek(1)[0]) # 1 =/= 3, not an issue but annoying
        qubits.append( network.nodes['4'].qmemory.peek(1)[0])
        print(qubits)
        qapi.combine_qubits(qubits)
        # #import pdb; pdb.set_trace()
        #print(qapi.reduced_dm(qubits))
        #print(qapi.reduced_dm(new_qubits))
        print(qapi.fidelity(qubits, gen_GHZ_ket(5), squared=True))
    elif(graph.name == "Twin graph"):
        qubits = []
        qubits.append( network.nodes['0'].qmemory.peek(0)[0])
        qubits.append( network.nodes['1'].qmemory.peek(1)[0])
        qapi.combine_qubits(qubits)
        print(qapi.fidelity(qubits, gen_GHZ_ket(2), squared=True))
    elif(graph.name == "Triangle graph"):
        qubits = []
        qubits.append( network.nodes['0'].qmemory.peek(0)[0])
        qubits.append( network.nodes['1'].qmemory.peek(1)[0])
        qubits.append( network.nodes['2'].qmemory.peek(1)[0])
        print(qubits)
        print(qapi.fidelity(qubits, gen_GHZ_ket(3), squared=True))
    print("all done")
