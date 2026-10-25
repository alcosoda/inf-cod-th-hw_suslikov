from fractions import Fraction
from math import lcm

def sample(dist, rng):
    # считаем общий знаменатель чтобы не терять точность на float
    D = lcm(*(p.denominator for p in dist.values()))
    r = rng.randrange(D)
    
    acc = 0
    for outcome, p in dist.items():
        acc += p.numerator * (D // p.denominator) # посчитанных в целых

        if acc > r:
            return outcome

def generate(src, rng):
    source = src["source"]
    L = len(source)
    i = 0
    while True:
        switch = source[i % L]
        model = sample(src["switches"][switch], rng)
        symbol = sample(src["models"][model], rng)
        yield symbol
        i += 1

def symbol_dist(src, t):
    source = src["source"]
    L = len(source)

    switch = source[t % L]

    dist = {}
    for model_name, p_model in src['switches'][switch].items():
        for symbol, p_symbol in src['models'][model_name].items():
            dist[symbol] = dist.get(symbol, Fraction(0)) + p_symbol * p_model
    return dist     

def block_prob(src, seq, start):
    
    p = 1
    for i, a in enumerate(seq):
        p_symbol = symbol_dist(src, start+i)[a]
        p *= p_symbol

    return p
