from SimulaQron.cqc.pythonLib.cqc import *
import math

class CoinflipConsensus:
    def __init__(self, queue):
        self.queue = queue

    def _atomic_flip(self, candidate1, candidate2, coeff):
        with CQCConnection(candidate1) as Alice:
            qcandidate1 = Alice.createEPR(candidate2)  # |00> + |11>.
            qcandidate1.X()
            
            # Bias
            angle = 2 * math.acos(coeff)
            qcandidate.rot_Y(angle * 256 / (2 * math.pi))

            # Measure the qubits.
            measured_value = qcandidate1.measure()

            # TODO: Is it right?
            # del qcandidate1

            if measured_value == 1:  # `candidate1` is a winner.
                return candidate1
            else:
                return candidate2

    def leader(self):
        assert queue.size >= 2

        winner = self.queue.pop()  # Returns "top" and removes it.

        for i in range(2, self.queue.size):
            coeff = 1 / math.sqrt(i)
            winner = self._atomic_flip(winner, elem, coeff)

        return winner
