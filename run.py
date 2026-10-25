# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #3 ===
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
    except SourceError as e:
        print(f"ошибка: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        # Страховка: программа не должна падать с трейсбеком ни на каком входе
        print(f"внутренняя ошибка: {e!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #3 ===
