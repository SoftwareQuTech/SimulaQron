from cqc.pythonLib_protocols.coinflip_leader import CoinflipConsensus


def main():
    """
        Creates array of four people and elects a leader among them using 
        the CoinFlipConsensus protocol.
        """
    arr = ["Alice", "Bob", "Charlie", "David"]
    leaderChooser = CoinflipConsensus(arr)
    return leaderChooser.leader()


# Runs 20 rounds of leader election and prints the results.
d = dict()
d["Alice"] = 0
d["Bob"] = 0
d["Charlie"] = 0
d["David"] = 0
for i in range(0, 20):
    if i % 10 == 0:
        print(i)
    d[main()] += 1
print(d)
