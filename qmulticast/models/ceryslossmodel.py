"""Define a loss model for Cerys analytic models."""

import math

import netsquid as ns
import numpy as np
from netsquid.components.models.errormodels import ErrorModel
from netsquid.components.models.qerrormodels import QuantumErrorModel
from netsquid.qubits import qubitapi as qapi
from netsquid.qubits.qformalism import QFormalism, get_qstate_formalism
from netsquid.qubits.qubit import Qubit
from netsquid.util import simtools as simtools


class CerysLossModel(QuantumErrorModel):
    """Model for exponential photon loss on fibre optic channels.

    Uses length of transmitting channel to sample an
    exponential loss probability.

    Parameters
    ----------
    p_loss_init : float, optional
        Initial probability of losing a photon once it enters a channel.
        e.g. due to frequency conversion.
    p_loss_length : float, optional
        Photon survival probability per channel length [dB/km].
    rng : :obj:`~numpy.random.RandomState` or None, optional
        Random number generator to use. If ``None`` then
        :obj:`~netsquid.util.simtools.get_random_state` is used.

    """

    def __init__(self, p_loss_init=0.2, p_loss_length=0.25, rng=None):
        super().__init__()
        self.p_loss_init = p_loss_init
        self.p_loss_length = p_loss_length
        self.rng = rng if rng else simtools.get_random_state()
        self.required_properties = ["length"]

    @property
    def rng(self):
        """ :obj:`~numpy.random.RandomState`: Random number generator."""
        return self.properties["rng"]

    @rng.setter
    def rng(self, value):
        if not isinstance(value, np.random.RandomState):
            raise TypeError("{} is not a valid numpy RandomState".format(value))
        self.properties["rng"] = value

    @property
    def p_loss_init(self):
        """float: initial probability of losing a photon when it enters channel."""
        return self.properties["p_loss_init"]

    @p_loss_init.setter
    def p_loss_init(self, value):
        if not 0 <= value <= 1:
            raise ValueError
        self.properties["p_loss_init"] = value

    @property
    def p_loss_length(self):
        """float: photon survival probability per channel length [dB/km]."""
        return self.properties["p_loss_length"]

    @p_loss_length.setter
    def p_loss_length(self, value):
        if value < 0:
            raise ValueError
        self.properties["p_loss_length"] = value

    def error_operation(self, qubits, **kwargs):
        """Error operation to apply to qubits.

        Parameters
        ----------
        qubits : tuple of :obj:`~netsquid.qubits.qubit.Qubit`
            Qubits to apply noise to.
        """
        # self.apply_loss(qubits, delta_time, **kwargs)
        for idx, qubit in enumerate(qubits):
            if qubit is None:
                continue

            prob_loss = 1 - (1 - self.p_loss_init) * np.exp(
                kwargs["length"] * np.log(0.1) / self.p_loss_length
            )

            self.lose_qubit(qubits, idx, prob_loss, rng=self.properties["rng"])
