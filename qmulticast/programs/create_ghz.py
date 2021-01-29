"""Program to entangle states to GHZ."""

import logging
import pdb

from netsquid.components.instructions import INSTR_CNOT, INSTR_MEASURE
from netsquid.components.qprogram import QuantumProgram

logger = logging.getLogger(__name__)

from typing import List


# TODO Use physical gates for noise
class CreateGHZ(QuantumProgram):
    """Turn the bell states into cool GHZ states"""

    def __init__(self, bell_qubits: List[int]) -> None:
        """Initialise.

        Parameters
        ----------
        bell_qubits : List[int]
            A list of memory positions to act upon.
        """
        super().__init__()
        self.bell_qubits = bell_qubits[1:]

    def program(self) -> None:
        """Create a GHZ state from qubits in memory."""
        logger.debug("Beginning GHZ creation.")
        logger.debug(f"Using qubits {self.bell_qubits}")

        for qubit in self.bell_qubits:
            self.apply(
                INSTR_CNOT, [0, qubit], physical=False, output_key=f"cnot-{qubit}"
            )

        for qubit in self.bell_qubits:
            self.apply(
                INSTR_MEASURE, qubit, output_key=f"measure-{qubit}", physical=False
            )
            logger.debug(f"Measurement on qubit %s", qubit)

        yield self.run()
