from fractions import Fraction

# my input data from time: 19-suslikov ivan
S = 19


def get_params(s):
    k = 5 - s % 3
    M = 2 + s % 3
    L = 3 + s % 5
    d = 1 + s % 3
    q = (2, 3, 5, 7)[s % 4]

    eps = Fraction(1, 10 ** (2 + s % 3))

    params = {}
    params["s"] = s
    params["k"] = k
    params["M"] = M
    params["L"] = L
    params["d"] = d
    params["q"] = q
    params["eps"] = eps

    return params


if __name__ == "__main__":
    print(get_params(S))
