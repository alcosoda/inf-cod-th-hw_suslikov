# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #2 ===
import argparse
import json
import math
import os
import random
import sys
import time
from fractions import Fraction
from itertools import islice

from ict.variant import S, get_params
from ict.source import load_source, SourceError
from ict.zmh import ZmhError
from ict.task11 import generate


def parse_n(text):
    """Значение --n: целое число или строка None."""
    if text == "None":
        return None
    try:
        return int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"ожидается целое число или None, получено {text!r}")


def cmd_generate(args):
    src = load_source(args.source)
    rng = random.Random(args.seed)
    symbols = generate(src, rng)
    # Однобуквенные символы печатаем слитно, иначе через пробел (иначе "1"+"01" == "10"+"1")
    sep = "" if all(len(a) == 1 for a in src["alphabet"]) else " "
    if args.n is not None and args.n > 0:
        print(sep.join(islice(symbols, args.n)))
    else:
        try:
            for symbol in symbols:
                print(symbol, end=sep, flush=True)
        except KeyboardInterrupt:
            print()


class UsageError(Exception):
    """Некорректные аргументы режима (не описание источника)."""


def fmt_frac(x):
    """Точная дробь + приближение; огромные дроби (длинные блоки) не печатаем целиком."""
    approx = f"{float(x):.6g}"
    if len(str(x)) <= 40:
        return f"{x}  ~ {approx}"
    return (f"~ {approx}  (точная дробь: числитель {len(str(x.numerator))} цифр, "
            f"знаменатель {len(str(x.denominator))} цифр)")


# Длины реализации для таблицы сходимости частотной оценки
TABLE_NS = [10 ** e for e in range(2, 7)]


def cmd_prob(args):
    # Импорт здесь, а не наверху: пока функции не написаны, режим generate продолжает работать
    from ict.task11 import block_prob, avg_block_prob, freq_estimates, period

    if args.n <= 0:
        raise UsageError(f"N должно быть > 0, получено {args.n}")
    seq = args.seq
    r = len(seq)
    if r > args.n:
        raise UsageError(f"длина последовательности r = {r} больше N = {args.n}: нет ни одного окна")

    src = load_source(args.source)
    unknown = sorted(set(seq) - set(src["alphabet"]))
    if unknown:
        print(f"предупреждение: символов {unknown} нет в алфавите источника, вероятность равна 0",
              file=sys.stderr)

    p_first = block_prob(src, seq, 0)
    p_avg = avg_block_prob(src, seq)
    # Одна реализация длины max(Ns) на всё: оценка для N и для таблицы -- её префиксы
    Ns = sorted(set([args.n] + TABLE_NS))
    rng = random.Random(args.seed)
    freqs = freq_estimates(src, seq, [N for N in Ns if N >= r], rng)

    print(f"последовательность: {' '.join(seq)}  (r = {r}, период = {period(src)}, seed = {args.seed})")
    print(f"1) Pr{{X1..Xr = a1..ar}}           = {fmt_frac(p_first)}")
    print(f"2) среднее по сдвигам в периоде    = {fmt_frac(p_avg)}")
    print(f"3) частотная оценка, N = {args.n:<8} = {fmt_frac(freqs[args.n])}")
    print()
    print(f"{'N':>8}  {'частота':>10}  {'|f - (1)|':>10}  {'|f - (2)|':>10}")
    for N in TABLE_NS:
        if N not in freqs:
            print(f"{N:>8}  {'нет окон (N < r)':>34}")
            continue
        f = freqs[N]
        print(f"{N:>8}  {float(f):>10.6f}  {float(abs(f - p_first)):>10.6f}  {float(abs(f - p_avg)):>10.6f}")


def parse_fraction(text):
    """Аргумент вида "3/2", "1.5", "1e-3" -> точная дробь."""
    try:
        return Fraction(text.replace("∕", "/").strip())
    except (ValueError, ZeroDivisionError):
        raise argparse.ArgumentTypeError(f"ожидается число или дробь, получено {text!r}")


def get_memoryless(src):
    """(P, None) для стационарного источника без памяти, иначе (None, причина)."""
    from ict.task12 import check_memoryless
    return check_memoryless(src)


def cmd_entropy(args):
    from ict.task12 import entropy

    src = load_source(args.source)
    P, reason = get_memoryless(src)
    if P is None:
        print(f"источник НЕ является стационарным источником без памяти: {reason}")
        return
    print("источник стационарен и не имеет памяти")
    print("распределение P:")
    for symbol, p in P.items():
        print(f"  {symbol!r}: {p}  ~ {float(p):.6f}")
    print(f"H(X) = {entropy(P) + 0.0:.6f} бит/символ  (k = {len(P)}, максимум log2 k = {math.log2(len(P)):.6f})")


def fmt_big(x, q, l):
    """Мощность кода q^l: целиком, если короткая, иначе как степень."""
    return str(x) if len(str(x)) <= 12 else f"{q}^{l}"


def multiset_permutations(counts, symbols):
    """Все различные блоки данного типа в лексикографическом порядке (для вывода кодовых слов)."""
    n = sum(counts)
    counts = list(counts)
    block = []

    def rec():
        if len(block) == n:
            yield tuple(block)
            return
        for i, s in enumerate(symbols):
            if counts[i]:
                counts[i] -= 1
                block.append(s)
                yield from rec()
                block.pop()
                counts[i] += 1
    yield from rec()


def to_base(x, q, l):
    """Номер x -> кодовое слово длины l в алфавите {0..q-1}."""
    digits = []
    for _ in range(l):
        x, d = divmod(x, q)
        digits.append(str(d))
    return " ".join(reversed(digits)) if q > 10 else "".join(reversed(digits))


def write_code_file(path, P, n, l, q, R, Pe, chosen, max_words=256):
    symbols = list(P)
    total = sum(take for _, take, _ in chosen)
    code = {
        "description": "Равномерный код источника без памяти (задача 1.2). Кодируемое множество -- "
                       "q^l наиболее вероятных блоков длины n. Блоки упорядочены по убыванию вероятности "
                       "типа, внутри типа -- лексикографически по алфавиту; номер блока i (с 0) "
                       "кодируется словом длины l -- записью i в системе счисления по основанию q. "
                       "Блок вне множества -- ошибка декодирования.",
        "alphabet": symbols,
        "P": {s: str(p) for s, p in P.items()},
        "n": n, "q": q, "l": l, "R": str(R),
        "codebook_size": total,
        "Pe": str(Pe),
        "Pe_approx": float(Pe),
        "types": [{"counts": dict(zip(symbols, counts)), "blocks_in_type": c, "blocks_taken": take}
                  for counts, take, c in chosen],
    }
    if total <= max_words:
        words, i = [], 0
        for counts, take, _ in chosen:
            for block, _ in zip(multiset_permutations(counts, symbols), range(take)):
                words.append({"block": " ".join(block), "word": to_base(i, q, l)})
                i += 1
        code["words"] = words
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(code, f, ensure_ascii=False, indent=2)
        f.write("\n")


def cmd_code(args):
    from ict.task12 import entropy, code_length, best_types

    params = get_params(args.s)
    R = args.rate
    eps = args.eps if args.eps is not None else params["eps"]
    q = args.q if args.q is not None else params["q"]
    if R < 0:
        raise UsageError(f"скорость R должна быть >= 0, получено {R}")
    if not 0 < eps < 1:
        raise UsageError(f"граница eps должна быть в (0, 1), получено {eps}")
    if q < 2:
        raise UsageError(f"мощность алфавита кодера q должна быть >= 2, получено {q}")
    if args.nmax < 1:
        raise UsageError(f"n_max должно быть >= 1, получено {args.nmax}")

    src = load_source(args.source)
    P, reason = get_memoryless(src)
    if P is None:
        raise UsageError(f"режим применим только к стационарному источнику без памяти: {reason}")
    H = entropy(P) + 0.0  # +0.0 убирает "-0.0" у вырожденного источника

    print(f"P = {{{', '.join(f'{s}: {p}' for s, p in P.items())}}},  H(X) = {H:.6f} бит/символ")
    print(f"R = {R} ~ {float(R):.6f} бит/символ,  q = {q},  eps = {eps},  n_max = {args.nmax}")
    print()
    print(f"{'n':>4}  {'l(n)':>5}  {'q^l':>14}  {'Pe(n)':>14}  Pe <= eps")

    start = time.perf_counter()
    rows = []
    for n in range(1, args.nmax + 1):
        l = code_length(n, R, q)
        K = q ** l
        chosen, covered = best_types(P, n, K)
        Pe = 1 - covered
        rows.append((n, l, K, Pe, chosen))
        print(f"{n:>4}  {l:>5}  {fmt_big(K, q, l):>14}  {float(Pe):>14.6e}  {'да' if Pe <= eps else ''}")
    elapsed = time.perf_counter() - start

    print()
    good = [n for n, _, _, Pe, _ in rows if Pe <= eps]
    if good:
        print(f"минимальное n с Pe(n) <= eps: n = {good[0]}")
    else:
        print(f"на отрезке n = 1..{args.nmax} нет n с Pe(n) <= eps")

    # Существует ли n0: Pe(n) <= eps для ВСЕХ n >= n0 -- определяется сравнением R и H
    tail = None
    for n, _, _, Pe, _ in reversed(rows):
        if Pe > eps:
            break
        tail = n
    if float(R) > H:
        print(f"R > H(X) ({float(R):.6f} > {H:.6f}): n0 СУЩЕСТВУЕТ -- по прямой теореме кодирования "
              f"Pe(n) -> 0 при n -> oo.", end=" ")
        print(f"На отрезке Pe(n) <= eps для всех n >= {tail}." if tail else
              f"На рассмотренном отрезке n <= {args.nmax} оно ещё не достигнуто.")
    elif float(R) < H:
        print(f"R < H(X) ({float(R):.6f} < {H:.6f}): n0 НЕ существует -- по обратной теореме "
              f"Pe(n) -> 1 при n -> oo, поэтому Pe(n) > eps для всех достаточно больших n.")
        if good:
            print(f"При этом при малых n условие выполняется (n = {', '.join(map(str, good[:10]))}"
                  f"{', ...' if len(good) > 10 else ''}) -- это не противоречит теореме: она асимптотическая.")
    else:
        print("R = H(X): граничный случай, теорема кодирования не гарантирует Pe(n) -> 0 "
              "(при ненулевой дисперсии -log2 P(X) Pe(n) не стремится к 0).")

    n_code = good[0] if good else args.nmax
    n, l, K, Pe, chosen = rows[n_code - 1]
    write_code_file(args.out, P, n, l, q, R, Pe, chosen)
    print(f"описание кода для n = {n} (l = {l}) записано в {args.out}")
    print(f"время расчёта таблицы: {elapsed:.2f} с")


def read_input(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError as e:
        raise UsageError(f"не удалось прочитать {path}: {e.strerror}") from None


def write_output(path, data):
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
    except OSError as e:
        raise UsageError(f"не удалось записать {path}: {e.strerror}") from None


def cmd_compress(args):
    from ict.zmh import compress
    from ict.task12 import entropy

    data = read_input(args.file)
    blob, st = compress(data)
    out = args.out or args.file + ".zmh"
    write_output(out, blob)
    print(f"{args.file} -> {out}: {len(data)} -> {len(blob)} байт")

    if args.stats:
        n = len(data)
        freqs, lengths = st["freqs"], st["lengths"]
        H = entropy({b: Fraction(c, n) for b, c in freqs.items()}) + 0.0 if n else 0.0
        avg = Fraction(sum(c * lengths[b] for b, c in freqs.items()), n) if n else Fraction(0)
        print(f"различных байт:               {len(freqs)}")
        print(f"эмпирическая энтропия H:      {H:.6f} бит/байт")
        print(f"средняя длина кода l_avg:     {float(avg):.6f} бит/байт  (l_avg - H = {float(avg) - H:.6f})")
        print(f"заголовок:                    {st['header']} байт")
        print(f"данные:                       {st['data']} байт ({st['bits']} бит)")
        if n:
            print(f"коэффициент сжатия:           {n / len(blob):.4f}  (исходный / сжатый; "
                  f"размер {'вырос' if len(blob) > n else 'уменьшился'} на {abs(len(blob) - n) / n:.2%})")
        else:
            print(f"коэффициент сжатия:           не определён (пустой файл, сжатый = {len(blob)} байт заголовка)")


def cmd_decompress(args):
    from ict.zmh import decompress

    blob = read_input(args.file)
    out = decompress(blob)
    if args.out:
        target = args.out
    else:
        target = args.file[:-4] if args.file.lower().endswith(".zmh") else args.file + ".out"
        if os.path.exists(target):
            # Не перезаписываем исходный файл: пишем рядом
            stem, ext = os.path.splitext(target)
            target = f"{stem}.restored{ext}"
    write_output(target, out)
    print(f"{args.file} -> {target}: восстановлено {len(out)} байт, целостность подтверждена (CRC-32 совпадает)")


def main():
    # Без этого на Windows при выводе в файл/пайп кириллица уходит в cp1251
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    # Общие для всех режимов аргументы
    # allow_abbrev=False: иначе argparse молча понимает "--s" как сокращение "--seed"
    common = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    common.add_argument("--seed", type=int, default=0, help="seed генератора случайных чисел (по умолчанию 0)")

    parser = argparse.ArgumentParser(description="ДЗ 1. Кодирование источников", allow_abbrev=False)
    parser.add_argument("--variant", action="store_true", help="вывести номер варианта и параметры")
    parser.add_argument("--s", type=int, default=S, help=f"номер студента (по умолчанию {S})")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("generate", parents=[common], allow_abbrev=False, help="1.1 режим 1: реализация источника")
    p.add_argument("source", help="файл с описанием источника (JSON)")
    p.add_argument("--n", type=parse_n, default=None, help="длина реализации; None или <= 0 -- до Ctrl+C")

    p = sub.add_parser("prob", parents=[common], allow_abbrev=False,
                       help="1.1 режим 2: точная вероятность блока и частотная оценка")
    p.add_argument("source", help="файл с описанием источника (JSON)")
    p.add_argument("--n", type=int, required=True, help="длина реализации для частотной оценки, N > 0")
    p.add_argument("--seq", nargs="+", required=True, help="символы блока через пробел: --seq 0 1 1")

    p = sub.add_parser("entropy", allow_abbrev=False,
                       help="1.2 режим 1: проверка 'стационарен и без памяти' и энтропия")
    p.add_argument("source", help="файл с описанием источника (JSON)")

    p = sub.add_parser("code", allow_abbrev=False,
                       help="1.2 режим 2: равномерный код, таблица Pe(n), минимальное n")
    p.add_argument("source", help="файл с описанием источника (JSON)")
    p.add_argument("--rate", "-R", type=parse_fraction, required=True, help="скорость R, бит/символ: 1.5 или 3/2")
    p.add_argument("--eps", type=parse_fraction, default=None, help="граница Pe (по умолчанию из варианта)")
    p.add_argument("--q", type=int, default=None, help="мощность алфавита кодера (по умолчанию из варианта)")
    p.add_argument("--nmax", type=int, default=50, help="максимальная длина блока (по умолчанию 50)")
    p.add_argument("--out", default="out/code.json", help="файл с описанием кода (по умолчанию out/code.json)")

    p = sub.add_parser("compress", allow_abbrev=False, help="1.3: сжатие файла в .zmh (Хаффман, 2 прохода)")
    p.add_argument("file", help="исходный файл")
    p.add_argument("--stats", action="store_true", help="вывести H, среднюю длину кода, размеры, коэффициент")
    p.add_argument("--out", default=None, help="имя .zmh (по умолчанию <файл>.zmh)")

    p = sub.add_parser("decompress", allow_abbrev=False, help="1.3: восстановление из .zmh с проверкой целостности")
    p.add_argument("file", help="файл .zmh")
    p.add_argument("--out", default=None,
                   help="куда записать (по умолчанию имя без .zmh; если файл есть -- <имя>.restored<расш>)")

    args = parser.parse_args()

    if args.variant:
        params = get_params(args.s)
        # Первая строка -- номер варианта (п. 1.3 задания), дальше параметры
        print(f"вариант: {params['s']}")
        print(", ".join(f"{name} = {value}" for name, value in params.items() if name != "s"))
        return 0
    if args.command is None:
        parser.print_help()
        return 2

    try:
        if args.command == "generate":
            cmd_generate(args)
        elif args.command == "prob":
            cmd_prob(args)
        elif args.command == "entropy":
            cmd_entropy(args)
        elif args.command == "code":
            cmd_code(args)
        elif args.command == "compress":
            cmd_compress(args)
        elif args.command == "decompress":
            cmd_decompress(args)
    except (SourceError, UsageError) as e:
        print(f"ошибка: {e}", file=sys.stderr)
        return 2
    except ZmhError as e:
        # Разные коды: 3 -- чужой формат, 4 -- обрезан, 5 -- повреждён
        print(f"ошибка ({e.kind}): {e}", file=sys.stderr)
        return {"чужой формат": 3, "файл обрезан": 4}.get(e.kind, 5)
    except KeyboardInterrupt:
        # KeyboardInterrupt -- не Exception, без этой ветки Ctrl+C дал бы трейсбек
        print("\nпрервано пользователем", file=sys.stderr)
        return 130
    except Exception as e:
        # Страховка: программа не должна падать с трейсбеком ни на каком входе
        print(f"внутренняя ошибка: {e!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #2 ===
