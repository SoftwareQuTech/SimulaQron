from SimulaQron.cqc.pythonLib.cqc import *

class CoinflipConsensus:
    def __init__(self, queue):
        self.queue = queue

    def _atomic_flip(self, candidate1, candidate2):
        with CQCConnection(candidate1) as Alice:
            qcandidate1 = Alice.createEPR(candidate2)  # |00> + |11>.
            qcandidate1.X()
            # Measure the qubits.
            measured_value = qcandidate1.measure()

            # TODO: Is it right?
            # del qcandidate1

            if measured_value == 1:  # `candidate1` is a winner.
                return candidate1
            else:
                return candidate2

    def leader(self, queue):
        winner = queue.pop()  # Returns "top" and removes it.

        for elem in queue:
            winner = self._atomic_flip(winner, elem)

        return winner
