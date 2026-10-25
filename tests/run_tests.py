# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #18 ===
"""Прогоняет программу на собственных тестах и пишет вывод в RESULTS.md.

    python tests/run_tests.py

Каждый тест -- команда run.py; в RESULTS.md попадают команда, код возврата и полный
вывод (stdout + stderr). Повреждённые .zmh для теста диагностик создаются здесь же в out/.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
ZMH = os.path.join(ROOT, "tests", "zmh")  # входы режима восстановления (в репозитории)

S = "tests/sources/"
F = "tests/files/"

SECTIONS = [
    ("Вариант", [
        "--variant",
        "--s 0 --variant",
    ]),
    ("1.1, режим 1: реализация источника", [
        f"generate {S}example2.json --n 60 --seed 1",
        f"generate {S}example2.json --n 60 --seed 1",
        f"generate {S}example2.json --n 60 --seed 2",
        f"generate {S}var_stationary.json --n 70 --seed 1",
        f"generate {S}var_nonstationary.json --n 70 --seed 1",
        f"generate {S}var_markov.json --n 70 --seed 1",
        f"generate {S}var_markov_nonstationary.json --n 70 --seed 1",
        f"generate {S}var_mixture.json --n 70 --seed 1",
        f"generate {S}var_mixture.json --n 70 --seed 5",
        f"generate {S}degenerate/one_symbol.json --n 20",
        f"generate {S}degenerate/zero_prob_symbol.json --n 20",
        f"generate {S}degenerate/deterministic_period.json --n 20",
        f"generate {S}degenerate/multichar_symbols.json --n 12 --seed 3",
        f"generate {S}degenerate/markov_multichar.json --n 12 --seed 3",
        f"generate {S}degenerate/unicode_slash.json --n 20",
        f"generate {S}degenerate/utf8_bom.json --n 20",
    ]),
    ("1.1, режим 2: точная вероятность и частотная оценка", [
        f"prob {S}example2.json --n 1000 --seq 0 0 --seed 1",
        f"prob {S}var_nonstationary.json --n 1000 --seq a b --seed 1",
        f"prob {S}var_stationary.json --n 1000 --seq a b --seed 1",
        f"prob {S}var_markov.json --n 1000 --seq a a --seed 1",
        f"prob {S}var_markov_nonstationary.json --n 1000 --seq a a --seed 1",
        f"prob {S}var_mixture.json --n 1000 --seq a a --seed 1",
        f"prob {S}var_mixture.json --n 1000 --seq a a --seed 5",
        f"prob {S}degenerate/deterministic_period.json --n 100 --seq a b",
        f"prob {S}degenerate/multichar_symbols.json --n 100 --seq 10 01",
        f"prob {S}example2.json --n 50 --seq 0 x",
        f"prob {S}example2.json --n 3 --seq 1 1 1",
    ]),
    ("1.1: некорректные входы", [
        *(f"generate {S}bad/{name} --n 5" for name in sorted(os.listdir(os.path.join(ROOT, S, "bad")))),
        "generate nonexistent.json --n 5",
        f"generate {S}example2.json --n abc",
        f"prob {S}example2.json --n 0 --seq 0",
        f"prob {S}example2.json --n 2 --seq 0 0 1",
    ]),
    ("1.2, режим 1: проверка источника и энтропия", [
        f"entropy {S}var_stationary.json",
        f"entropy {S}var_nonstationary.json",
        f"entropy {S}var_markov.json",
        f"entropy {S}var_mixture.json",
        f"entropy {S}task12/five_symbols.json",
        f"entropy {S}task12/binary.json",
        f"entropy {S}task12/uniform4.json",
        f"entropy {S}degenerate/one_symbol.json",
        f"entropy {S}example2.json",
    ]),
    ("1.2, режим 2: равномерный код", [
        f"code {S}var_stationary.json --rate 2.5 --out out/code_r2.5.json",
        f"code {S}var_stationary.json --rate 1.99 --out out/code_r1.99.json",
        f"code {S}var_stationary.json --rate 1.95 --out out/code_r1.95.json",
        f"code {S}var_stationary.json --rate 1.95 --eps 3/20 --out out/code_r1.95_eps.json",
        f"code {S}task12/five_symbols.json --rate 2 --out out/code_five.json",
        f"code {S}task12/binary.json --rate 2/3 --q 2 --nmax 3 --eps 1/10 --out out/code_binary.json",
        f"code {S}task12/uniform4.json --rate 2 --q 2 --nmax 10 --out out/code_uniform.json",
        f"code {S}degenerate/one_symbol.json --rate 0 --nmax 5 --out out/code_one.json",
        f"code {S}var_mixture.json --rate 1",
        f"code {S}var_stationary.json --rate -1",
        f"code {S}var_stationary.json --rate 1 --q 1",
        f"code {S}var_stationary.json --rate 1 --eps 2",
    ]),
    ("1.3: сжатие (--stats) и восстановление", [
        cmd
        for name in ("ru.txt", "en.txt", "image.png", "repeat.bin", "empty.bin", "random.bin", "two_symbols.bin")
        for cmd in (f"compress {F}{name} --stats --out out/{name}.zmh",
                    f"decompress out/{name}.zmh --out out/{name}.restored")
    ]),
    ("1.3: повреждённые, чужие и обрезанные файлы", [
        "decompress tests/zmh/ru.txt.zmh --out out/ru_from_tests.txt",
        "decompress tests/zmh/broken_foreign.zmh",
        "decompress tests/zmh/broken_tiny.zmh",
        "decompress tests/zmh/broken_version.zmh",
        "decompress tests/zmh/broken_trunc_header.zmh",
        "decompress tests/zmh/broken_trunc_data.zmh",
        "decompress tests/zmh/broken_flip_data.zmh",
        "decompress tests/zmh/broken_flip_header.zmh",
        "decompress tests/zmh/broken_extra.zmh",
        "decompress tests/zmh/broken_flip_padding.zmh",
        "decompress tests/zmh/broken_empty.zmh",
        "decompress nonexistent.zmh",
        "compress nonexistent.txt",
    ]),
    ("Проверка ручных задач: код Хаффмана для заданных весов", [
        "huffman 5 3 2 1 1 1",
        "huffman 1/2 1/4 1/8 1/8",
        "huffman 1/3 0.25 5/12",
        "huffman 7",
        "huffman 1 1",
        "huffman 0 1",
        "huffman 1 abc",
    ]),
]


def run(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "run.py", *args.split()], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout + r.stderr).rstrip()


def make_broken():
    """Кладёт out/ru.txt.zmh в tests/zmh/ и портит его разными способами (после сжатия ru.txt)."""
    blob = open(os.path.join(OUT, "ru.txt.zmh"), "rb").read()
    os.makedirs(ZMH, exist_ok=True)
    with open(os.path.join(ZMH, "ru.txt.zmh"), "wb") as f:
        f.write(blob)

    def w(name, data):
        with open(os.path.join(ZMH, f"broken_{name}.zmh"), "wb") as f:
            f.write(data)

    w("foreign", open(os.path.join(ROOT, F, "image.png"), "rb").read())
    w("tiny", b"ZM")
    w("version", b"ZMH\x07" + blob[4:])
    w("trunc_header", blob[:20])
    w("trunc_data", blob[:-100])
    x = bytearray(blob); x[len(blob) // 2 + 300] ^= 0x10; w("flip_data", bytes(x))
    x = bytearray(blob); x[6] ^= 0x01; w("flip_header", bytes(x))
    w("extra", blob + b"\x00")
    x = bytearray(blob); x[-1] ^= 0x01; w("flip_padding", bytes(x))
    w("empty", b"")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(OUT, exist_ok=True)
    lines = ["# RESULTS", "",
             "Вывод программы на собственных тестах. Сгенерировано `python tests/run_tests.py`, руками не правится.",
             "Коды возврата: 0 — успех, 2 — некорректный вход, 3 — чужой формат, 4 — обрезан, 5 — повреждён.", ""]
    failures = 0
    for title, cmds in SECTIONS:
        if title.startswith("1.3: повреждённые"):
            make_broken()
        lines += [f"## {title}", ""]
        for cmd in cmds:
            code, out = run(cmd)
            if "внутренняя ошибка" in out or "Traceback" in out:
                failures += 1
            lines += [f"`python run.py {cmd}` → код {code}", "", "```", out, "```", ""]
            print(f"[{code}] {cmd}")
    # Побайтная проверка восстановления
    lines += ["## 1.3: побайтное сравнение восстановленных файлов", ""]
    pairs = [(F + name, f"out/{name}.restored")
             for name in ("ru.txt", "en.txt", "image.png", "repeat.bin", "empty.bin", "random.bin", "two_symbols.bin")]
    pairs.append((F + "ru.txt", "out/ru_from_tests.txt"))
    for src, restored in pairs:
        same = open(os.path.join(ROOT, src), "rb").read() == open(os.path.join(ROOT, restored), "rb").read()
        lines.append(f"- {src} = {restored}: {'совпадает' if same else 'НЕ СОВПАДАЕТ'}")
        failures += not same
    with open(os.path.join(ROOT, "RESULTS.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"RESULTS.md записан; внутренних ошибок/расхождений: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #18 ===
