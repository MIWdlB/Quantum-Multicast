"""Useful functions."""

# define a generic GHZ
import numpy as np
def gen_GHZ_ket(n):
    k = 2**n
    x = np.zeros((k,1),dtype=complex)
    x[k-1] = 1
    x[0] = 1
    #return = KetRepr(x)/np.sqrt(2)
    return x/np.sqrt(2)