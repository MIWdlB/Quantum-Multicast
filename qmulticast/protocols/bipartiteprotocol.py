"""Defines the protocol to be followed at a node bipartite source(s)"""
import logging
import operator
from functools import reduce
from typing import List, Optional

from netsquid.components.component import Port
from netsquid.components.instructions import INSTR_X
from netsquid.components.qprogram import QuantumProgram
from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol
from netsquid.protocols.protocol import Signals
from netsquid.qubits.qubitapi import fidelity, reduced_dm
from netsquid.util.simlog import get_loggers

from qmulticast.programs import CreateGHZ
from qmulticast.utils import fidelity_from_node, gen_GHZ_ket
from qmulticast.utils.functions import log_entanglement_rate

from .inputprotocol import InputProtocol

logger = logging.getLogger(__name__)

handler = logging.FileHandler(filename="fidelity-data.txt", mode="w")

res_logger = logging.Logger(name="results")
res_logger.addHandler(handler)


class BipartiteProtocol(NodeProtocol):
    """Class defining the protocol of a bipartite network node.

    If the node is a source, send out entangled qubits and transform to GHZ.
    If the node is a reciever, await incoming qubit and classical message.
    """

    def __init__(
        self,
        node: Node,
        name: Optional[str] = None,
        source: bool = False,
        receiver: bool = True,
        repeater: bool = False,
    ):
        """Initialise the protocol wiht information about the node.

        Parameters
        ----------
        node : Node
            The node on which to run this protocol.
        name : Optional[str]
            The name of this protocol.
        source : bool, default = True
            Whether this node should act as a source.
            If not the node is a reciever.
        """
        logger.debug(f"Initialising Bipartite protocol for node {node.name}.")
        super().__init__(node=node, name=name)

        self._output = source
        self._input = receiver

        if self._output:
            self.add_subprotocol(BipartiteOutputProtocol(self.node))

        if self._input:
            self.add_subprotocol(InputProtocol(self.node, repeater=repeater))

    def run(self):
        """Run the protocol."""
        node = self.node
        logger.debug(f"Running bipartite protocol on node {node.name}.")
        self.start_subprotocols()


class BipartiteOutputProtocol(NodeProtocol):
    """Defines behaviour of node when outputting qubits"""

    def __init__(self, node: Node, name: Optional[str] = None):
        super().__init__(node=node, name=name)

        mem_ports = self.node.qmemory.ports
        self.q_out_ports = [
            value for key, value in self.node.ports.items() if "qout" in key
        ]

        self.source_mem = [
            mem_ports[f"qin{num}"] for num in range(0, len(self.q_out_ports) * 2, 2)
        ]
        self.source_names = [
            f"qsource-{port.name.lstrip('qout-')}" for port in self.q_out_ports
        ]
        self.fidelity = fidelity_from_node(self.node)

    def _trigger_all_sources(self) -> None:
        """Trigger all sources on the node."""
        logger.debug("Triggering all sources.")

        try:
            routes = self.node.routing_table[self.node.name]
        except:
            routes = self.node.routing_table[int(self.node.name)]
        
        for source_name in self.source_names:
            # Trigger the source
            source = self.node.subcomponents[source_name]
            _, here, channel_end = source_name.split("-")
            source.output_meta["origin"] = here 
            source.output_meta["dest"] = []
            
            for destination, forward_node in routes.items():
                #import pdb; pdb.set_trace()
                if channel_end == (forward_node:= str(forward_node)):
                    source.output_meta["dest"] += str(destination)
                    source.trigger()
                    logger.debug(f"Triggered source {source.name} for destination node {destination}.")

    def _send_all_delete(self) -> None:
        """Send a classical message to each reciever node."""
        logger.debug("Sending delete instruction to all nodes.")
        for port_name, port in self.node.ports.items():
            if "cout" in port_name:
                edge = port_name.lstrip("cout-")
                port.tx_output(f"Delete qubit {edge}")

    def _do_corrections(self, output: dict) -> None:
        """Correct qubits for GHZ state creation."""
        logger.debug("Completing corrections.")
        network = self.node.supercomponent

        for record, value in output.items():
            if "measure" in record:
                # If the measurement is 0 do nothing.
                if value == [0]:
                    logger.debug("No correction for measure %s", record)
                    continue
                
                logger.debug("Correcting for measure %s", record)
                qubit_no = int(record.lstrip("measure-"))
                qubit = self.node.qmemory.peek(qubit_no)[0]

                edgenodes = qubit.name.split("-")[1:3]
                end_name = edgenodes[-1]
                edge_name = "-".join(edgenodes)

                end_qmemory = network.nodes[end_name].qmemory
                qubit = end_qmemory.get_matching_qubits("edge", value=edge_name)

                if len(qubit) == 0:
                    logger.warning("Could not find qubit on node %s", end_name)
                    logger.debug("Skipping run.")
                    continue

                end_qmemory.execute_instruction(
                    instruction = INSTR_X,
                    qubit_mapping = qubit,
                    physical = False
                )
                logger.debug("Completed correction on node %s", end_name)

    def run(self) -> None:
        """The protocol to be run by a source node."""
        logger.debug(f"Running Output protocol.")

        while True:

            await_all_sources = [
                self.await_port_input(port) for port in self.source_mem
            ]
            self._trigger_all_sources()
            yield reduce(operator.and_, await_all_sources)
            logger.debug("Got all memory input from sources.")

            # Do entanglement
            bell_qubits = [
                pos for pos in self.node.qmemory.used_positions if pos % 2 == 0
            ]
            prog = CreateGHZ(bell_qubits)
            logger.debug(f"Executing program with qubits {bell_qubits}")
            self.node.qmemory.execute_program(prog)
            yield self.await_program(self.node.qmemory)
            logger.debug("Program complete, output %s.", prog.output)

            # TODO how do we find the minimum wait time needed in a sensible way?
            # Could await on ports using
            #self.node.subcomponents['qsource-edge'].ports['qout1'].connected_port
            yield self.await_timer(1e5)
            self._do_corrections(prog.output)
            next(self.fidelity)

            # self._send_all_delete()
            logger.debug("Clearing local memory.")
            [self.node.qmemory.pop(index) for index in self.node.qmemory.used_positions]
