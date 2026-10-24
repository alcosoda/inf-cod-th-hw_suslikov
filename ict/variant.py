# my input data from time: 19-suslikov ivan
s = 19

k = 5 - s % 3
M = 2 + s % 3
L = 3 + s % 5
d = 1 + s % 3
q = (2, 3, 5, 7)[s % 4]

import fractions
eps = fractions.Fraction(1, 10 ** (2 + s % 3))

if __name__ == "__main__":
    print(f"s: {s}")
    print(f"k: {k}")
    print(f"M: {M}")
    print(f"L: {L}")
    print(f"d: {d}")
    print(f"q: {q}")
    print(f"eps: {eps}")
    