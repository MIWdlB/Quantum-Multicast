"""Defines the protocol to be followed at a node bipartite source(s)"""
import operator
import logging
from functools import reduce

from netsquid.protocols import NodeProtocol
from netsquid.nodes import Node
from netsquid.components.instructions import INSTR_EMIT

from qmulticast.protocols.report_input import MoveInput

logger = logging.getLogger(__name__)


class BipartiteProtocol(NodeProtocol):
    """Class defining the protocol of a bipartite network node.

    First draft I'll assum it's the twin graph
    """

    def __init__(self, node: Node, name=None, source: bool = False):
        """Initialise the protocol wiht information about the node."""
        logger.debug(f"Initialising Bipartite protocol for node {node.name}.")
        super().__init__(node=node, name=name)

    
        self.input_ports = [
            port for port in self.node.qmemory.ports if "qin" in port
        ]
        self.input_ports.remove("qin")
        self.input_ports = [
            port for port in self.input_ports 
            if int(port.lstrip("qin")) % 2 == 1
            ]


        self.output_ports = [
            port for port in self.node.ports.values() if "out" in port.name
        ]

        self._is_source = source
        self._mem_size = self.node.qmemory.num_positions

        # for port_num in range(self._mem_size):
        #     # We assume input memory ports are the odd numbers.
        #     if port_num % 2 == 1:
        #         logger.debug("Adding move protocol for port %s", port_num)
        #         self.add_subprotocol(
        #             MoveInput(self.node, node.qmemory.ports[f"qin{port_num}"])
        #         )

    def run(self):
        """Run the protocol."""
        node = self.node
        logger.debug(f"Running bipartite protocol on node {node.name}.")
        logger.debug(f"Node: {self.node.name} " + f"has {self._mem_size} memory slots.")

        
        while True:
        # Send from source.
        # - out to all connection ports.
            if self._is_source:
                for port in self.output_ports:
                    logger.debug(f"Found port {port.name}")
                    edge = port.name.lstrip("out-")

                    # Trigger the source
                    source_name = "qsource-" + edge
                    self.node.subcomponents[source_name].trigger()
                    logger.debug(f"Triggered source {source_name}.")

            # Get input
            await_any_input = [self.await_port_input(self.node.qmemory.ports[port]) for port in self.input_ports]
            # if self.node.name == "0":
            #     import pdb;pdb.set_trace()
            yield reduce(operator.or_, await_any_input)
            
            logger.debug(f"Got input: memory useage {self.node.qmemory.used_positions}")
            print(f"Node {self.node.name} used memory: {self.node.qmemory.used_positions}")

            # Entangle inputs with INSTR_SWAP


        # while True:
        #     for mem_pos in self.node.qmemory.:
        #         # Iterate in reverse so that input_mem_pos is handled last
        #         if self._is_source:
        #             self.node.subcomponents[self._qsource_name].trigger()
        #         yield self.await_port_input(self._qmem_input_port)
        #         if mem_pos != self._input_mem_pos:
        #             self.node.qmemory.execute_instruction(
        #                 INSTR_SWAP, [self._input_mem_pos, mem_pos]
        #             )
        #             if self.node.qmemory.busy:
        #                 yield self.await_program(self.node.qmemory)
        #         self.entangled_pairs += 1
        #         self.send_signal(Signals.SUCCESS, mem_pos)

        # Entangle swap.
        # - entangle swap with node to ensure that
