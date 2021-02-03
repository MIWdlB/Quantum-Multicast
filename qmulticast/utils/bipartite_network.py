"""Defines a function to create and return a bipartite source network from a Graph.

TODO maybe make this a subclass of the Network class and build things in init.
    That'd be neater but not high prority.
"""

import logging
from typing import Hashable, Dict, Any, Tuple

import netsquid.qubits.ketstates as ks
from netsquid.components import ClassicalChannel, QuantumChannel, QuantumProcessor
from netsquid.components.models.delaymodels import FibreDelayModel, FixedDelayModel
from netsquid.components.models.qerrormodels import DepolarNoiseModel, FibreLossModel
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.nodes import Network, Node
from netsquid.qubits.state_sampler import StateSampler
from netsquid.util.simlog import get_loggers

from networkx import DiGraph

logger = logging.getLogger(__name__)

def unpack_edge_values(node: str, graph: DiGraph) -> Tuple[Hashable, Hashable, Dict[Hashable, Any]]:
    """Return the start, end and weight of a nodes edges."""
    logger.debug("Unpacking edges.")
    
    edges = {}
    for edge in graph.edges.data():
        start, stop, weight = edge[0], edge[1], edge[2].get('weight', 1)
        if str(start) != node.name:
            continue
        if type(weight) not in [int, float]:
            raise TypeError("Edge weights must be numeric.")
        edges[stop] = weight

    return edges
        
def create_bipartite_network(name: str, graph: DiGraph) -> Network:
    """Turn graph into netsquid network.

    Give each node a bipatite source for each edge, assign memory
    size and redirect to memory slots from connection ports.

    Parameters
    ----------
    name : str
        The name of the network.
    graph : Graph
        Graph representing the desired network.

    Returns
    -------
    Network
        A netsquid Network object.
    """
    logger.debug("Creating Network.")

    # First set up NetSquid node objects for each graph node.
    nodes = {node_name: Node(str(node_name)) for node_name in graph.nodes}

    # Delay models to use for components.
    source_delay = FixedDelayModel(delay=0)
    fibre_delay = None  # FibreDelayModel()

    # Set up a state sampler for the |B00> bell state.
    state_sampler = StateSampler([ks.b00], [1.0])

    # Noise models to use for components.
    # TODO find a suitable rate
    depolar_noise = None  # DepolarNoiseModel(depolar_rate=1e-21)
    source_noise = depolar_noise
    # TODO do we want to change the default values?
    fibre_loss = None  # FibreLossModel()

    # Set up a Network object
    network = Network(name=name)
    logger.debug("Adding nodes to network.")
    network.add_nodes([n for n in nodes.values()])

    # Add unique components to each node
    logger.debug("Adding unique components to nodes.")
    for node_name, node in nodes.items():

        # node_name = node.name
        logger.debug(f"Node: {node_name}.")

        node_connections = unpack_edge_values(node, graph)

        # Names need to be strings for NetSquid object names
        node_name = str(node_name)

        mem_size = len(node_connections) * 2
        # Add a quantum memory to each of the nodes.
        # TODO how much memory do we want to give?
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

        node_connections = unpack_edge_values(node, graph)

        # Add channels
        logger.debug("Adding connections.")
        # Iterate over memory positions
        mem_position = 0
        for end, length in node_connections.items():
            # need the names as a string for the channel
            node_name = str(node_name)
            end_name = str(end)
            edge_name = node_name + "-" + end_name

            # Quantum connection
            logger.debug(f"Creating quantum channel 'qchannel-{edge_name}.")
            q_channel = QuantumChannel(
                name=f"qchannel-{edge_name}",
                length=length,
                models={
                    "delay_model": fibre_delay,
                    "quantum_loss_model": fibre_loss,
                    "quantum_noise_model": depolar_noise,
                },
            )

            logger.debug(f"Adding quantum connection on edge {edge_name}.")
            out_port, _ = network.add_connection(
                node_name,
                end_name,
                channel_to=q_channel,
                label=f"Q-{edge_name}",
                bidirectional=False,
                port_name_node1=f"qout-{edge_name}",
                port_name_node2=f"qin-{edge_name}",
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
                output_meta={"edge": edge_name},
            )
            node.add_subcomponent(qsource)

            logger.debug("Redirecting qsource ports.")
            qsource.ports["qout0"].forward_output(node.ports[out_port])
            qsource.ports["qout1"].connect(
                node.subcomponents["qmemory"].ports[f"qin{mem_position}"]
            )
            mem_position += 2

            # Classical connection
            logger.debug(f"Creating classical channel 'cchannel-{edge_name}'.")
            c_channel = ClassicalChannel(
                name=f"cchannel-{edge_name}",
                length=length,
                models={
                    "delay_model": fibre_delay,
                },
            )

            logger.debug(f"Adding classical connectin on edge {edge_name}.")
            network.add_connection(
                node_name,
                end_name,
                channel_to=c_channel,
                label=f"C-{edge_name}",
                bidirectional=False,
                port_name_node1=f"cout-{edge_name}",
                port_name_node2=f"cin-{edge_name}",
            )

    # Now go through each node and assign the port
    # for the input from each channel.
    for node_name, node in nodes.items():
        logger.debug(f"Forawrding input for node {node_name}.")
        mem_position = 1
        for port in node.ports.values():
            if "out" in port.name:
                continue
            if "cin" in port.name:
                continue

            logger.debug("Redirecting input port to memory %s.", mem_position)

            # Now from the connection we need to redirect the qubit to the
            # qmemory of the recieving node.
            # TODO how do we assing it to an empyty memory slot.

            port.forward_input(
                node.subcomponents["qmemory"].ports[f"qin{mem_position}"]
            )
            mem_position += 2

    return network
