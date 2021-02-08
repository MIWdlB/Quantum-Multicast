"""Defines a function to create and return a bipartite source network from a Graph.

TODO maybe make this a subclass of the Network class and build things in init.
    That'd be neater but not high prority.
"""

import logging
from typing import Hashable, Dict, Any, Tuple

import netsquid.qubits.ketstates as ks
from netsquid.components import QuantumChannel, QuantumProcessor, ClassicalChannel
from netsquid.components.models.delaymodels import (FibreDelayModel,
                                                    FixedDelayModel)
from netsquid.components.models.qerrormodels import (DepolarNoiseModel,
                                                     FibreLossModel)
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.nodes import Network, Node
from netsquid.qubits.state_sampler import StateSampler

from qmulticast.models.ceryslossmodel import CerysLossModel

from networkx import DiGraph
import csv
from .functions import gen_GHZ_ket

logger = logging.getLogger(__name__)

def create_network(name: str, graph: DiGraph, output_file: str, bipartite: bool) -> Network:
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

    # Set up a Network object
    network = Network(name=name)
    logger.debug("Adding nodes to network.")
    network.add_nodes([n for n in nodes.values()])

    network.source_type = "bipartite" if bipartite else "multipartite"
    network.output_file = output_file
    network.graph = graph

    # Delay and noise models to use for components.
    p_loss_length = 2
    p_loss_init = 0.2

    models = {
        "source_delay": FixedDelayModel(delay=0),
        "source_noise": None,
        "fibre_delay": FibreDelayModel(),
        "fibre_loss": CerysLossModel(p_loss_init, p_loss_init),
        "depolar_noise": DepolarNoiseModel(1e7),
    }

    # Set up state sampler.
    if bipartite:
        state = [ks.b00]
    else:
        n_qubits = graph.out_degree["0"] + 1
        state = gen_GHZ_ket(n_qubits)
    
    state_sampler = StateSampler(state)

    logger.debug(f"Writing network data to file {output_file}.")
    with open(output_file, mode="a") as file:
        writer = csv.writer(file)
        data = [graph.out_degree['0'], graph.length, p_loss_length, p_loss_init]
        writer.writerow(data)

    logger.debug("Adding unique components to nodes.")
    for node_name, node in nodes.items():
        add_processor(node, graph, models)
        
        if not bipartite:
            add_mulitpartite_source(node, graph, models, state_sampler)

    # We need more than one of some components because of
    # the network topology.
    logger.debug("Adding non-unique components to nodes.")
    for node_name, node in nodes.items():
        add_connections(node, graph, models)
        
        if bipartite:
            add_bipartite_sources(node, graph, models, state_sampler)

        # We now need to redirect input
        redirect_outputs(node, graph)
        redirect_inputs(node)

    return network

def unpack_edge_values(
    node: str, graph: DiGraph
) -> Tuple[Hashable, Hashable, Dict[Hashable, Any]]:
    """Return the start, end and weight of a nodes edges."""
    logger.debug("Unpacking edges.")

    edges = {}
    for edge in graph.edges.data():
        start, stop, weight = edge[0], edge[1], edge[2]["weight"]
        if str(start) != node.name:
            continue
        edges[stop] = weight
    logger.debug("Found edges: %s", edges)

    return edges

def add_processor(node: Node, graph: DiGraph, models: dict) -> None:
    """ Add a processor to the node"""
    # node_name = node.name
    logger.debug(f"Node: {node.name}.")

    node_connections = unpack_edge_values(node, graph)

    # Names need to be strings for NetSquid object names
    node_name = str(node.name)

    mem_size = len(node_connections)*2 # input and output
    # Add a quantum memory to each of the nodes.
    logger.debug(f"Adding quantum memory 'qmemory-{node_name}'")
    logger.debug(f"\tsize: {mem_size}")
    qmemory = QuantumProcessor(
        name="qmemory",
        num_positions=mem_size,
        memory_noise_models=models["depolar_noise"],
    )

    node.add_subcomponent(qmemory)

def add_mulitpartite_source(node: Node, graph: DiGraph, models: Dict, state_sampler: StateSampler):
    node_name = node.name
    logger.debug(f"Adding QSource for node 'qsource-{node_name}'.")
    num_ports = state_sampler._num_qubits

    qsource = QSource(
        name=f"qsource-{node_name}",
        state_sampler=state_sampler,
        models={
            "emission_delay_model": models["source_delay"],
            "emissions_noise_model": models["source_noise"],
        },
        num_ports=num_ports, # size of GHZ state? each qubit goes to a out port
        status=SourceStatus.EXTERNAL,
        output_meta={"origin": node_name}
    )
    node.add_subcomponent(qsource)

    # add first qubit to local mem
    qsource.ports["qout0"].connect(
        node.subcomponents["qmemory"].ports[f"qin{0}"]
    )


def add_connections(node: Node, graph: DiGraph , models: Dict):
    logger.debug(f"Node: {node.name}")

    network = node.supercomponent

    node_connections = unpack_edge_values(node, graph)

    # Add channels
    logger.debug("Adding connections.")
    # Iterate over memory positions
    for end, length in node_connections.items():
        # need the names as a string for the channel
        node_name = str(node.name)
        end_name = str(end)
        edge_name = node_name + "-" + end_name

        logger.debug(f"Creating channel 'qchannel-{edge_name}.")
        qc_channel = QuantumChannel(
            name=f"qchannel-{edge_name}",
            length=length,
            models={
                "delay_model": models["fibre_delay"],
                "quantum_loss_model": models["fibre_loss"],
                "quantum_noise_model": models["depolar_noise"],
            },
        )
        logger.debug(f"Adding network connection on edge {edge_name}.")
        network.add_connection(
            node_name,
            end_name,
            channel_to=qc_channel,
            label=f"Q-{edge_name}",
            bidirectional=False,
            port_name_node1=f"qout-{edge_name}",
            port_name_node2=f"qin-{edge_name}",
        )

        # Classical connection
        logger.debug(f"Creating classical channel 'cchannel-{edge_name}'.")
        c_channel = ClassicalChannel(
            name=f"cchannel-{edge_name}",
            length=length,
            models={
                "delay_model": None,
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


def add_bipartite_sources(node: Node, graph: DiGraph, models: Dict, state_sampler: StateSampler) -> None:
    node_connections = unpack_edge_values(node, graph)

    for end in node_connections.keys():
        node_name = str(node.name)
        end_name = str(end)
        edge_name = node_name + "-" + end_name

        # Add a bipartite source.
        qsource = QSource(
            name=f"qsource-{edge_name}",
            state_sampler=state_sampler,
            models={
                "emission_delay_model": models["source_delay"],
                "emissions_noise_model": models["source_noise"],
            },
            num_ports=2,
            status=SourceStatus.EXTERNAL,
            output_meta={"edge": edge_name, "origin": node_name},
        )
        node.add_subcomponent(qsource)


def redirect_outputs(node: Node, graph: DiGraph):
    mem_position = 0
    node_output = 1
    node_connections = unpack_edge_values(node, graph)

    network = node.supercomponent

    for end in node_connections.keys():
        node_name = str(node.name)
        end_name = str(end)
        edge_name = node_name + "-" + end_name

        if network.source_type == "bipartite":
            logger.debug("Redirecting qsource ports.")

            qsource = node.subcomponents[f"qsource-{edge_name}"]

            qsource.ports["qout0"].forward_output(node.ports[f"qout-{edge_name}"])
            qsource.ports["qout1"].connect(
                node.subcomponents["qmemory"].ports[f"qin{mem_position}"]
            )
            mem_position += 2

        if network.source_type == "multipartite":
            logger.debug("Redirecting qsource ports.")
            node.subcomponents[f"qsource-{node_name}"].ports[f"qout{node_output}"].forward_output(node.ports[f"qout-{edge_name}"])
            node_output += 1

def redirect_inputs(node: Node) -> None:
    """Redirect input ports to qmemory."""
    # Now go through each node and assign the port
    # for the input from each channel.
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