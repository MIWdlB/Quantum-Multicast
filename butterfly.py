import netsquid as ns
from netsquid.components import Channel, QuantumChannel, CombinedChannel
from netsquid.components import QuantumMemory
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.nodes import Node, Network
import pydynaa
import numpy as np
import netsquid.qubits.ketstates as ks
from netsquid.qubits.state_sampler import StateSampler
from netsquid.components.models.delaymodels import FixedDelayModel, FibreDelayModel
from netsquid.components.models.qerrormodels import DepolarNoiseModel, FibreLossModel

from qmulticast.utils import Graph, TwinGraph, ButterflyGraph

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

def create_network(name: str, graph: Graph):
    """Turn graph into netsquid nodes."""
    logger.debug("Creating Network.")

    # First set up NetSquid node objects for each graph node.
    nodes = {node_name: Node(str(node_name)) for node_name in graph.nodes}

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
        logger.debug(f"Node {node_name}")

        num_connections = len(graph.edges[node_name])

        # Set up a state sampler for the |B00> bell state.
        state_sampler = StateSampler([ks.b00], [1.0])

        node_name = str(node_name)

        # Add a quantum memory to each of the nodes.
        qmemory = QuantumMemory(
            f"node-{node_name}-memory",
            num_positions=num_connections,
            memory_noise_models=[depolar_noise, depolar_noise],
        )
        network.nodes[node_name].add_subcomponent(qmemory, name=f"node-qmemory")

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
            status=SourceStatus.EXTERNAL
        )

            # We can get the ports for the connection by using nework.get_connected_ports


if __name__ == "__main__":
    init_logs()
    butterfly = ButterflyGraph()
    create_network("butterfly bipartite", butterfly)
