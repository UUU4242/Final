from pdptw import PDPTW
from alns import ALNS

testI = "Instances/lr109.txt"
problem = PDPTW.readInstance(testI)

# Static parameters
nDestroyOps = 10
nRepairOps = 3
minSizeNBH = 1
nIterations = 5000

# Parameters to tune:
maxPercentageNHB = 5
tau = 0.07
coolingRate = 0.9995
decayParameter = 0.15
noise = 0.015

alns = ALNS(problem, nDestroyOps, nRepairOps, nIterations, minSizeNBH, maxPercentageNHB, tau, coolingRate, decayParameter, noise)
alns.execute()
