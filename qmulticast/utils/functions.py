"""Helper functions."""

# define a generic GHZ
import logging

import numpy as np
import csv
import netsquid as ns
from netsquid.nodes import Node,Network
from netsquid.qubits.dmtools import DMRepr
from netsquid.qubits.qrepr import convert_to
from netsquid.qubits.qubitapi import fidelity, reduced_dm
from netsquid.util.simtools import sim_time
import netsquid.qubits.qubitapi as qapi
from netsquid.qubits.qubitapi import fidelity, reduced_dm, measure, discard
from netsquid.util.simtools import sim_time, sim_stop

logger = logging.getLogger(__name__)

res_logger = logging.Logger(name='results', level=logging.ERROR)
fhandler = logging.FileHandler(filename="results.txt", mode='w')
formatter = logging.Formatter(
    "%(asctime)s:%(levelname)s:%(filename)s - %(message)s"
)
fhandler.setFormatter(formatter)
res_logger.addHandler(fhandler)

def gen_GHZ_ket(n) -> np.ndarray:
    """Create a GHZ state of n qubits.
    Wants a list returned in the form of weights of each element of ket 
    e.g. |X> =  0.5|00> + 0|01> + 0|10> 0.5|11> => [[0.5],[0],[0],[0.5]]
    Parameters
    ----------
    n : int
        The number of qubits.
    """
    k = 2 ** n
    x = np.zeros((k, 1), dtype=complex)
    x[k - 1] = 1
    x[0] = 1
    return x / np.sqrt(2)


def fidelity_from_node(source: Node) -> float:
    """Calculate the fidelity of GHZ state creation.

    Parameters
    ----------
    node : Node
        The node object to treat as source.
    """
    logger.debug(f"Calculating fidelity of GHZ state from source {source}")
    vals = np.array([])

    network = source.supercomponent # hack
    recievers = [str(reciever) for _, reciever in network.graph.out_edges(source.name)]
    
    # define multipartite receivers 

    rate = log_entanglement_rate()
    next(rate)
    yield
    run = 0
    hits = 0
    lost_qubits = 0
    entanglement_rate = None
    min_time = None
    mean_time = None
    time_std = None
    mean_fidelity = None
    loss_rate = None
    fidelity_std = None
    while True:
        if run == 1:
            min_time = sim_time(ns.SECOND)
        elif run == 2:
            second_time = sim_time(ns.SECOND)
            min_time = second_time-min_time

        run +=1
        qubits = []
        qmems = []
        for node in network.nodes.values():
                if node is source:
                    # Assume that the source has a qubit
                    # and that it's in the 0 position.
                    qubits += node.qmemory.peek(0)
                    qmems.append(node.qmemory)

                if node.name in recievers:
                    mem_pos = node.qmemory.get_matching_qubits(
                        "origin", value=source.name
                    )
                    if not mem_pos:
                        logger.debug("Node %s has not recieved a qubit.", node.name)
                        lost_qubits += 1
                    qubits += node.qmemory.peek(mem_pos)
                    qmems.append(node.qmemory)

        # Bit ugly this walrus but I haven't been able to
        # use it yet and I think it's cute.
        if (lq := len(qubits)) - (le := len(recievers)) != 1:
            logger.warning("Some GHZ qubits were lost!")
            logger.warning("Number of edges: %s", le)
            logger.warning("Number of qubits: %s (expecting %s)", lq, (le+1))
            
        else:
            hits += 1
            logger.debug("GHZ Qubit(s) %s", qubits)
            fidelity_val = fidelity(qubits, gen_GHZ_ket(len(qubits)), squared=True)
            vals = np.append(vals, fidelity_val)
            mean_fidelity = np.mean(vals)

            loss_rate = lost_qubits/(run*(len(recievers)+1))
            # dm = convert_to(qubits, DMRepr)
            res_logger.info(f"Run {run} Fidelity: {fidelity_val}")
            res_logger.info(f"Average Fidelity: {mean_fidelity}")
            res_logger.info(f"Qubit loss rate: {loss_rate}")
            logger.info(f"Run {run} Fidelity: {fidelity_val}")
            logger.info(f"Average Fidelity: {mean_fidelity}")
            logger.info(f"Qubit loss rate: {loss_rate}")
            fidelity_std = np.std(vals)
            
            mean_time, time_std = next(rate)

            res_logger.debug("Average Run time: %s", mean_time)
            logger.debug("Average Run time: %s", time_std)
            res_logger.debug("Min Run time: %s", min_time)
            logger.debug("Min Run time: %s", min_time)

            if mean_time == 0:
                logger.warning("No time has passed - entanglement rate infinite.") 
                res_logger.warning("No time has passed - entanglement rate infinite.") 
            elif min_time and mean_time:
                res_logger.info(f"Entanglement Rate: {min_time/mean_time}Hz")
                logger.info(f"Entanglement Rate: {min_time/mean_time}Hz")

        # Clean up by getting rid of qubits
        logger.debug("Discarding qubits.")
        for qmem in qmems:
            qmem.reset()
        for qubit in qubits:
            discard(qubit)

        if hits >= 200 or run >= 100000:
            logger.debug("Logging results.")
            # assumes we have defined these at the top of the file.
            with open(network.output_file, mode="a") as file:
                writer = csv.writer(file)
                if min_time and mean_time:
                    entanglement_rate = min_time/mean_time
                data = [hits, mean_fidelity, fidelity_std, loss_rate, min_time, mean_time, time_std, entanglement_rate]
                writer.writerow(data)
            sim_stop()
        
        yield

def log_entanglement_rate():
    """Generator to find the entanglement rate."""
    vals = np.array([sim_time(ns.SECOND)])
    logger.info("Entanglement rate initialised.")
    yield

    while True:
        time = sim_time(ns.SECOND)
        vals = np.append(vals, time)
        res_logger.debug("Run time: %s", vals[-1] - vals[-2])
        logger.debug("Run time: %s", vals[-1] - vals[-2])
        # Take mean difference so that we get more
        # accurate over time.
        mean_diff = np.mean(vals[1:] - vals[0:-1])
        res_logger.debug("Average Run time: %s", mean_diff)
        logger.debug("Average Run time: %s", mean_diff)
        
        std = np.std(vals)
        output = (mean_diff, std)

        yield output