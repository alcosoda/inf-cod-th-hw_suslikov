# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #2 ===
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
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #2 ===
