import time

from SimulaQron.cqc.pythonLib.protocols.coinflip_leader import CoinflipConsensus

#####################################################################################################
#
# main
#
def main():
        arr = ["Alice", "Bob","Charlie","David"]
        leaderChooser = CoinflipConsensus(arr)
        return leaderChooser.leader()
        
##################################################################################################
d = dict()
d['Alice'] = 0
d['Bob'] = 0
d['Charlie'] = 0
d['David'] = 0
for i in range(0,20):
        if i % 10 == 0:
                print(i)
        d[main()] += 1
print(d)

