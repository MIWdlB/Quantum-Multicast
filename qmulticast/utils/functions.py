"""Helper functions."""

# define a generic GHZ
import numpy as np


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
