import netsquid as ns
from netsquid.components import Channel, QuantumChannel, CombinedChannel
from netsquid.components import QuantumMemory, QSource, SourceStatus
from netsquid.nodes import Node, Network
import pydynaa
import numpy as np
import netsquid.qubits.ketstates as ks
from netsquid.qubits.state_sampler import StateSampler
from netsquid.components.models.delaymodels import FixedDelayModel, FibreDelayModel
from netsquid.components.models.qerrormodels import DepolarNoiseModel, FibreLossModel

from qmulticast.utils.graph import Graph

ns.set_random_state(seed=123456789)


import logging
def init_logs() -> None:
    logging.basicConfig(
        filename="logs.txt", 
        filemode="w", 
        format="%(asctime)s:%(filename)s:%(levelname)s - %(message)s",
        level=logging.DEBUG,
        )

    global logger
    logger = logging.getLogger(__name__)

def build_butterfly() -> Graph:
    """Create a butterfly graph."""
    logger.debug("Creating butterfly graph.")

    # We want 5 nodes
    nodes = {0, 1, 2, 3, 4}
    butterfly = Graph(nodes)

    # The top left of the bowtie is 0, 1 is below
    # 2 is the centre
    # 3 is opposite 0 on the top right
    # 4 is on the bottom right
    butterfly.addEdge(start=0, end=1)
    butterfly.addEdge(start=0, end=2)
    butterfly.addEdge(start=1, end=2)
    butterfly.addEdge(start=2, end=3)
    butterfly.addEdge(start=2, end=4)
    butterfly.addEdge(start=3, end=4)

    butterfly.showEdges()

    return butterfly


def create_network(name: str, graph: Graph):
    """Turn graph into netsquid nodes."""
    logger.debug("Creating Network.")

    # First set up NetSquid node objects for each graph node.
    nodes = {node_name: Node(str(node_name)) for node_name in graph.nodes}

    # Set up a state sampler for the |B00> bell state.
    state_sampler = StateSampler([ks.b00], [1.0])

    # Delay models to use for components.
    source_delay = FixedDelayModel(delay=0)
    fibre_delay = FibreDelayModel()

    # Noise models to use for components.
    # TODO find a suitable rate
    depolar_noise = DepolarNoiseModel(depolar_rate=1e-4)
    source_noise = depolar_noise
    # TODO do we want to change the default values?
    fibre_loss = FibreLossModel()

    # Set up a Network object
    network = Network(name=name)
    logger.debug("Adding nodes to network.")
    network.add_nodes([n for n in nodes.values()])

    # Add components to each node
    for node_name, node in nodes.items():

        # Add channels
        logger.debug("Adding connections.")
        for end, weight in graph.edges[node_name].items():
            # need the names as a string for the channel
            node_name = str(node_name)
            end_name = str(end)

            qc_channel = CombinedChannel(
                name=f"qchannel-{node_name}-{end_name}",
                length=weight,
                models={
                    "delay_model": fibre_delay,
                    "quantum_loss_model": fibre_loss,
                    "quantum_noise_model": depolar_noise,
                },
            )
            # This will add unidirectional channels
            # which is what the Graph class tracks.
            network.add_connection(
                node_name, end_name, channel_to=qc_channel, label=f"{node_name}-{end}"
            )
            logger.debug(f"Added connection {node_name}-{end}.")


    # Add components to each node
    logger.debug("Adding components to nodes.")
    for node_name, node in nodes.items():
        # Add a quantum memory to each of the nodes.
        qmemory = QuantumMemory(
            f"node-{node_name}-memory",
            num_positions=2,
            memory_noise_model=[depolar_noise, depolar_noise],
        )
        node.add_subcomponent(qmemory, name=f"node-qmemory")

        # Add a source to each of the nodes.
        qsource = QSource(
            name=f"node-{node_name}-qsource",
            state_sampler=state_sampler,
            models={
                "emission_delay_model": source_delay,
                "emissions_noise_model": source_noise,
            },
            num_ports=len(graph.edges[node_name]),
            status=SourceStatus.External
        )

            # We can get the ports for the connection by using nework.get_connected_ports


if __name__ == "__main__":
    init_logs()
    butterfly = build_butterfly()
    create_network("butterfly bipartite", butterfly)
