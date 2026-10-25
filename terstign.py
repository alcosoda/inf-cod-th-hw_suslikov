from math import log2

def entropy(P):
    return sum(float(p) * log2(float(p)) for p in P if p != 0 )

entropy([-0.1, 0.5, 0.2])