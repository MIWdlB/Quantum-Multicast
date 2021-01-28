from qmulticast.utils.graphlibrary import RepeaterGraph, TriangleGraph
import netsquid as ns
import netsquid.qubits.ketstates as ks
import numpy as np
import pydynaa
from netsquid.components import (
    Channel,
    CombinedChannel,
    QuantumChannel,
    QuantumProcessor,
)
from netsquid.components.models.delaymodels import FibreDelayModel, FixedDelayModel
from netsquid.components.models.qerrormodels import DepolarNoiseModel, FibreLossModel
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.nodes import Network, Node
from netsquid.qubits.state_sampler import StateSampler
from netsquid.protocols import Protocol
from netsquid.examples.entanglenodes import EntangleNodes

from qmulticast.utils import ButterflyGraph, Graph, TwinGraph
from qmulticast.protocols import BipartiteProtocol

ns.set_random_state(seed=12345678)


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
    depolar_noise = None#DepolarNoiseModel(depolar_rate=1e-21)
    source_noise = depolar_noise
    # TODO do we want to change the default values?
    fibre_loss = None#FibreLossModel()

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

        mem_size = len(node_connections) * 2 + 1
        # Add a quantum memory to each of the nodes.
        # TODO how much memory do we want to give?
        # TODO change this to a processor as in tutorial "A full simulation"
        logger.debug(f"Adding quantum memory 'qmemory-{node_name}'")
        logger.debug(f"\tsize: {mem_size}")
        qmemory = QuantumProcessor(
            name="qmemory",
            num_positions=mem_size,
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
        # Iterate over memory positions
        mem_position = 0
        for end, length in node_connections.items():
            # need the names as a string for the channel
            node_name = str(node_name)
            end_name = str(end)
            edge_name = node_name + "-" + end_name

            logger.debug(f"Creating channel 'qchannel-{edge_name}.")
            qc_channel = QuantumChannel(
                name=f"qchannel-{edge_name}",
                length=length,
                models={
                    "delay_model": fibre_delay,
                    "quantum_loss_model": fibre_loss,
                    "quantum_noise_model": depolar_noise,
                },
            )

            logger.debug(f"Adding network connection on edge {edge_name}.")
            out_port, _ = network.add_connection(
                node_name,
                end_name,
                channel_to=qc_channel,
                label=edge_name,
                bidirectional=False,
                port_name_node1=f"out-{edge_name}",
                port_name_node2=f"in-{edge_name}",
            )

            logger.debug(f"Adding QSource for connection 'qsource-{edge_name}'.")
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
            qsource.ports["qout1"].connect(
                node.subcomponents["qmemory"].ports[f"qin{mem_position}"]
            )
            mem_position += 2

    # Now go through each node and assign the port
    # for the input from each channel.
    for node_name, node in nodes.items():
        logger.debug(f"Forawrding input for node {node_name}")
        mem_position = 1
        for port in node.ports.values():
            if "out" in port.name:
                continue
            logger.debug("Redirecting input port to memory %s", mem_position)

            # Now from the connection we need to redirect the qubit to the
            # qmemory of the recieving node.
            # TODO how do we assing it to an empyty memory slot.
            # import pdb; pdb.set_trace()

            port.forward_input(
                node.subcomponents["qmemory"].ports[f"qin{mem_position}"]
            )
            mem_position += 2

    return network


def create_ghz(network: Network) -> None:
    """Create an entangled graph state."""
    # TODO should we be making a measurement?

    # First create a state

    # Forward to port?

    # Entanglement swap
    # What's the correct way to create a GHZ?

    protocols = []
    # import pdb; pdb.set_trace()
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
    # q = network.nodes['0'].qmemory.peek(0)
    # q1 = network.nodes['0'].qmemory.peek(1)

    # print(q, q1)


if __name__ == "__main__":
    init_logs()
    logger.debug("Starting programme.")
    graph = ButterflyGraph()
    logger.debug("Created graph.")
    network = create_network("bipartite-butterfly", graph)
    logger.debug("Created Network.")
    network = create_ghz(network)
    logger.debug("GHZ created.")
