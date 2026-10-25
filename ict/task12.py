from fractions import Fraction
from math import log2, lcm, comb

from ict.task11 import symbol_dist


# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #11 ===
def check_memoryless(src):
    """(P, None), если источник стационарный без памяти; иначе (None, причина)."""
    if src['type'] == "markov":
        return None, "марковский источник имеет память: символ зависит от предыдущих d символов"
    if src['type'] == "mixture":
        # Смесь одинаковых источников без памяти -- это тот же источник без памяти
        dists = [check_memoryless(comp) for _, comp in src["components"]]
        if all(P is not None for P, _ in dists) and all(P == dists[0][0] for P, _ in dists):
            return dists[0][0], None
        return None, ("смесь: компонента выбирается один раз на всю реализацию, поэтому символы "
                      "на разных тактах зависимы (источник с памятью, неэргодический)")
    if src['type'] == "switching":
        # Символы на разных тактах независимы всегда (выборы на тактах независимы),
        # поэтому стационарность = одинаковое распределение символа на всех фазах периода
        P = {a: p for a, p in symbol_dist(src, 0).items() if p != 0}
        for t in range(1, len(src["source"])):
            Pt = {a: p for a, p in symbol_dist(src, t).items() if p != 0}
            if Pt != P:
                return None, (f"источник не стационарен: распределение символа на такте {t} "
                              f"{fmt_dist(Pt)} отличается от такта 0 {fmt_dist(P)}")
        return P, None
    raise ValueError("Неправильный тип сорса")


def fmt_dist(P):
    return "{" + ", ".join(f"{a}: {p}" for a, p in P.items()) + "}"
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #11 ===


def entropy(P):
    return -sum(float(p) * log2(float(p)) for p in P.values() if p != 0)  # fix .values(): Claude, SOURCES.md #11


# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #11 ===
def code_length(n, R, q):
    """l(n) = floor(n R / log2 q) без float: наибольшее l, при котором q^l <= 2^(nR).
    При R = a/b возводим обе части в степень b: q^(l b) <= 2^(n a) -- сравнение целых."""
    a, b = R.numerator, R.denominator
    l = 0
    while q ** ((l + 1) * b) <= 2 ** (n * a):
        l += 1
    return l


def best_types(P, n, K):
    """K наиболее вероятных блоков длины n через типы блоков.

    Тип (n_1..n_k) -- сколько раз встречается каждый символ. Все блоки типа
    равновероятны, поэтому K лучших блоков = целые типы по убыванию вероятности
    + часть следующего типа. Типов C(n+k-1, k-1) вместо k^n блоков.

    Точность: p_i = a_i / D (D -- общий знаменатель), вероятность блока = w / D^n,
    где w = a_1^n_1 ... a_k^n_k -- целое. Сортируем и суммируем целые w, делим в конце.

    Возвращает (chosen, covered): chosen -- [(counts, взято блоков, всего блоков в типе)]
    по убыванию вероятности, covered -- Fraction, суммарная вероятность взятых блоков."""
    probs = list(P.values())
    k = len(probs)
    D = lcm(*(p.denominator for p in probs))
    a = [p.numerator * (D // p.denominator) for p in probs]
    powers = [[ai ** j for j in range(n + 1)] for ai in a]  # a_i^j заранее

    types = []  # (w, число блоков, counts)

    def rec(i, left, w, count, counts):
        # i -- текущий символ, left -- сколько позиций блока ещё не распределено,
        # w и count -- накопленные произведения по символам 0..i-1
        if i == k - 1:  # последний символ забирает остаток
            types.append((w * powers[i][left], count, counts + (left,)))
            return
        for ni in range(left + 1):
            # C(left, ni): куда в оставшихся left позициях поставить ni символов i
            rec(i + 1, left - ni, w * powers[i][ni], count * comb(left, ni), counts + (ni,))

    rec(0, n, 1, 1, ())
    types.sort(key=lambda t: t[0], reverse=True)

    chosen = []
    left_K = K
    S = 0
    for w, count, counts in types:
        if left_K == 0:
            break
        take = min(count, left_K)
        S += take * w
        left_K -= take
        chosen.append((counts, take, count))
    return chosen, Fraction(S, D ** n)
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #11 ===
