import netsquid as ns
import netsquid.qubits.ketstates as ks
import numpy as np
import pydynaa
from netsquid.components import Channel, CombinedChannel, QuantumChannel, QuantumMemory
from netsquid.components.models.delaymodels import FibreDelayModel, FixedDelayModel
from netsquid.components.models.qerrormodels import DepolarNoiseModel, FibreLossModel
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.nodes import Network, Node
from netsquid.qubits.state_sampler import StateSampler
from netsquid.protocols import Protocol
from netsquid.examples.entanglenodes import EntangleNodes

from qmulticast.utils import ButterflyGraph, Graph, TwinGraph

ns.set_random_state(seed=123456789)


import logging


def init_logs() -> None:
    logging.basicConfig(
        filename="logs.txt",
        filemode="w",
        format="%(asctime)s:%(levelname)s:%(filename)s - %(message)s",
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

    # Add unique components to each node
    logger.debug("Adding unique components to nodes.")
    for node_name, node in nodes.items():

        # node_name = node.name
        logger.debug(f"Node: {node_name}.")

        node_connections = graph.edges[node_name]

        # Names need to be strings for NetSquid object names
        node_name = str(node_name)

        # Add a quantum memory to each of the nodes.
        # TODO how much memory do we want to give?
        # TODO change this to a processor as in tutorial "A full simulation"
        logger.debug(f"Adding quantum memory 'qmemory-{node_name}'")
        qmemory = QuantumMemory(
            name="qmemory",
            num_positions=len(node_connections) * 2,
            memory_noise_models=depolar_noise,
        )
        node.add_subcomponent(qmemory)

    # We need more than one of some components because of
    # the network topology.
    logger.debug("Adding non-unique components to nodes.")
    for node_name, node in nodes.items():

        # node_name = node.name
        logger.debug(f"Node: {node_name}")

        node_connections = graph.edges[node_name]

        # Add channels
        logger.debug("Adding connections.")
        for end, length in node_connections.items():
            # need the names as a string for the channel
            node_name = str(node_name)
            end_name = str(end)
            end_node = network.nodes[end_name]
            edge_name = node_name + "-" + end_name

            logger.debug(f"Creating channel 'qchannel-{edge_name}.")
            qc_channel = CombinedChannel(
                name=f"qchannel-{edge_name}",
                length=length,
                models={
                    "delay_model": fibre_delay,
                    "quantum_loss_model": fibre_loss,
                    "quantum_noise_model": depolar_noise,
                },
            )

            logger.debug(f"Adding network connection on edge {edge_name}.")
            out_port, in_port = network.add_connection(
                node_name,
                end_name,
                channel_to=qc_channel,
                label=edge_name,
                bidirectional=False,
                port_name_node1=f"out-{edge_name}",
                port_name_node2=f"in-{edge_name}",
            )

            logger.debug(f"Adding QSource for connection 'qsource-{node_name}'.")
            qsource = QSource(
                name=f"qsource-{edge_name}",
                state_sampler=state_sampler,
                models={
                    "emission_delay_model": source_delay,
                    "emissions_noise_model": source_noise,
                },
                num_ports=2,
                status=SourceStatus.EXTERNAL,
            )
            node.add_subcomponent(qsource)

            # Turns out this is more difficult cause we need to
            # prevent ourselves overwriting memory
            logger.debug("Redirecting qsource ports.")
            # Now redirect from the source to the ports
            # First one goes out to the output port

            qsource.ports["qout0"].forward_output(node.ports[out_port])
            # second one goes to the first memory register.
            qsource.ports["qout1"].connect(node.subcomponents["qmemory"].ports["qin0"])

            logger.debug("Redirecting input port.")
            # Now from the connection we need to redirect the qubit to the
            # qmemory of the recieving node.
            # TODO how do we assing it to an empyty memory slot.
            end_node.ports[in_port].forward_input(
                end_node.subcomponents["qmemory"].ports["qin"]
            )

    return network


def create_ghz(network: Network) -> None:
    """Create an entangled graph state."""
    # TODO should we be making a measurement?

    # First create a state

    # Forward to port?

    # Entanglement swap
    # What's the correct way to create a GHZ?

    # Let's try it out with an example
    print(ns.examples.entanglenodes.__file__)


if __name__ == "__main__":
    init_logs()
    graph = TwinGraph()
    network = create_network("bipartite-butterfly", graph)
    network = create_ghz(network)
