import netsquid as ns
import netsquid.qubits.ketstates as ks
import numpy as np
import pydynaa
from netsquid.components import (Channel, CombinedChannel, QuantumChannel,
                                 QuantumMemory)
from netsquid.components.models.delaymodels import (FibreDelayModel,
                                                    FixedDelayModel)
from netsquid.components.models.qerrormodels import (DepolarNoiseModel,
                                                     FibreLossModel)
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.nodes import Network, Node
from netsquid.qubits.state_sampler import StateSampler

from qmulticast.utils import ButterflyGraph, Graph, TwinGraph

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


def create_network(name: str, graph: Graph) -> Network:
    """Turn graph into netsquid nodes."""
    logger.debug("Creating Network.")

    # First set up NetSquid node objects for each graph node.
    nodes = {node_name: Node(str(node_name)) for node_name in graph.nodes}

    # Delay models to use for components.
    source_delay = FixedDelayModel(delay=0)
    fibre_delay = FibreDelayModel()

    # Set up a state sampler for the |B00> bell state.
    state_sampler = StateSampler([ks.b00], [1.0])

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
    logger.debug("Adding components to nodes.")
    for node_name, _ in nodes.items():
        logger.debug(f"Node {node_name}")

        node_connections = graph.edges[node_name]

        # Names need to be strings for NetSquid object names
        node_name = str(node_name)

        # Add channels
        logger.debug("Adding connections.")
        for end, weight in node_connections.items():
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
            # which is what the Graph class describes.
            network.add_connection(
                node_name, end_name, channel_to=qc_channel, label=f"{node_name}-{end}"
            )
            logger.debug(f"Added connection {node_name}-{end}.")
            # We can get the ports for the connection by using nework.get_connected_ports

        # Add a quantum memory to each of the nodes.
        qmemory = QuantumMemory(
            f"node-{node_name}-memory",
            num_positions=len(node_connections),
            memory_noise_models=[depolar_noise] * len(node_connections),
        )
        network.nodes[node_name].add_subcomponent(qmemory, name=f"node-{node_name}-qmemory")

        # Add a source to each of the nodes
        # for each connection!
        qsource = QSource(
            name=f"node-{node_name}-qsource",
            state_sampler=state_sampler,
            models={
                "emission_delay_model": source_delay,
                "emissions_noise_model": source_noise,
            },
            num_ports=2,
            status=SourceStatus.EXTERNAL,
        )
        network.nodes[node_name].add_subcomponent(qsource, name=f"node-{node_name}-qsource")


def create_ghz(network: Network) -> None:
    """Create an entangled graph state."""
    pass

if __name__ == "__main__":
    init_logs()
    graph = TwinGraph()
    network = create_network("butterfly bipartite", graph)

