# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #2 ===
import argparse
import random
import sys
from itertools import islice

from ict.variant import S, get_params
from ict.source import load_source, SourceError
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

    args = parser.parse_args()

    if args.variant:
        for name, value in get_params(args.s).items():
            print(f"{name} = {value}")
        return 0
    if args.command is None:
        parser.print_help()
        return 2

    try:
        if args.command == "generate":
            cmd_generate(args)
        elif args.command == "prob":
            cmd_prob(args)
    except (SourceError, UsageError) as e:
        print(f"ошибка: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        # Страховка: программа не должна падать с трейсбеком ни на каком входе
        print(f"внутренняя ошибка: {e!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #2 ===
