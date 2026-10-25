from fractions import Fraction
from math import lcm
from collections import deque

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
        # === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #3 ===
        # Символа может не быть в распределении такта (нет в алфавите или модели
        # этой фазы его не выдают) -- тогда его вероятность ровно 0, а не KeyError
        p_symbol = symbol_dist(src, start+i).get(a, Fraction(0))
        # === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #3 ===
        p *= p_symbol

    return p



def avg_block_prob(src, seq):
    L = len(src["source"])
    return sum(block_prob(src, seq, j) for j in range(L)) / L



def freq_estimates(src, seq, Ns, rng):
    r = len(seq)
    target = list(seq)
    window = deque(maxlen=r)
    count = 0
    result = {}
    N_max = max(Ns)

    for i, symbol in enumerate(generate(src, rng), start=1):
        window.append(symbol)
        if i >= r  and list(window) == target:
            count += 1
        if i in Ns:
            result[i] = Fraction(count, i-r+1)
        if i == N_max:
            return result