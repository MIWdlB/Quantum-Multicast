"""Helper functions."""

# define a generic GHZ
import logging

import numpy as np
import netsquid as ns
from netsquid.nodes import Node
from netsquid.qubits.dmtools import DMRepr
from netsquid.qubits.qrepr import convert_to
from netsquid.qubits.qubitapi import fidelity, reduced_dm, measure, discard
from netsquid.util.simtools import sim_time, sim_stop

logger = logging.getLogger(__name__)

res_logger = logging.Logger(name='results', level=logging.DEBUG)
fhandler = logging.FileHandler(filename="results.txt", mode='w')
formatter = logging.Formatter(
    "%(asctime)s:%(levelname)s:%(filename)s - %(message)s"
)
fhandler.setFormatter(formatter)
res_logger.addHandler(fhandler)

def gen_GHZ_ket(n) -> np.ndarray:
    """Create a GHZ state of n qubits.

    Parameters
    ----------
    n : int
        The number of qubits.
    """
    k = 2 ** n
    x = np.zeros((k, 1), dtype=complex)
    x[k - 1] = 1
    x[0] = 1
    # return = KetRepr(x)/np.sqrt(2)
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

    network = source.supercomponent

    edges = [
        name.lstrip("qsource-")
        for name in source.subcomponents.keys()
        if "qsource" in name
    ]
    recievers = {edge.split("-")[-1]: edge for edge in edges}

    rate = log_entanglement_rate()
    yield

    run = 0
    lost_qubits = 0
    min_time = None
    while True:
        if run > 2:
            pass
        elif run == 1:
            first_time = sim_time(ns.SECOND)
        elif run == 2:
            second_time = sim_time(ns.SECOND)
            min_time = second_time-first_time

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
                    "edge", value=recievers[node.name]
                )
                if not mem_pos:
                    logger.debug("Node %s has not recieved a qubit.", node.name)
                    lost_qubits += 1
                qubits += node.qmemory.peek(mem_pos)
                qmems.append(node.qmemory)

        # Bit ugly this walrus but I haven't been able to
        # use it yet and I think it's cute.
        if (lq := len(qubits)) - (le := len(edges)) != 1:
            logger.warning("Some GHZ qubits were lost!")
            logger.warning("Number of edges: %s", le)
            logger.warning("Number of qubits: %s (expecting %s)", lq, (le+1))
            
        else:
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
            
            mean_time = next(rate)

            res_logger.debug("Min Run time: %s", min_time)
            logger.debug("Min Run time: %s", min_time)

            if mean_time == 0:
                logger.error("No time has passed - entanglement rate infinite.") 
                res_logger.error("No time has passed - entanglement rate infinite.") 
            elif min_time and mean_time:
                res_logger.info(f"Entanglement Rate: {min_time/mean_time}Hz")
                logger.info(f"Entanglement Rate: {min_time/mean_time}Hz")

        # Clean up by getting rid of qubits
        logger.debug("Discarding qubits.")
        for qmem in qmems:
            qmem.reset()
        for qubit in qubits:
            discard(qubit)

        if run >= 100:
            with open("statistics.txt", mode="a") as file:
                file.writelines("runs, mean_fidelity, loss_rate, min_time, mean_time\n")
                file.writelines(f"{run}, {mean_fidelity}, {loss_rate}, {min_time}, {mean_time}\n")
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
        yield mean_diff
