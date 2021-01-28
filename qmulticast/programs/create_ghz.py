"""Program to entangle states to GHZ"""

from netsquid.components.qprogram import QuantumProgram
from netsquid.components.instructions import INSTR_CNOT, INSTR_H, INSTR_MEASURE

import logging
import pdb

logger = logging.getLogger(__name__)

from typing import List

#TODO Use physical gates for noise
class CreateGHZ(QuantumProgram):
    """Turn the bell states into cool GHZ states"""

    def __init__(self, bell_qubits: List[int]):
        """Initialise"""
        super().__init__()

        self.bell_qubits = bell_qubits

    def program(self):
        logger.debug("Beginning GHZ creation.")
        logger.debug(f"Using qubits {self.bell_qubits}")


        for qubit in self.bell_qubits:
            if qubit == 0:
                continue
            self.apply(INSTR_CNOT, [0, qubit], physical = False, output_key=f"cnot-{qubit}")
        self.apply(INSTR_H, 0)

        for qubit in self.bell_qubits:
            #pdb.set_trace()
            self.apply(INSTR_MEASURE, qubit, output_key=f"measure-{qubit}", physical = False)
            logger.debug(f"Measurement on qubit %s", qubit)

        yield self.run()



