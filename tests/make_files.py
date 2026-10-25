# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #14 ===
"""Создаёт тестовые файлы задачи 1.3 в tests/files/ (воспроизводимо).

    python tests/make_files.py

Тексты на русском и английском лежат в репозитории готовыми (ru.txt, en.txt);
скрипт создаёт изображение, файл из одного байта, пустой и случайный файлы.
zlib используется ТОЛЬКО здесь -- чтобы получить настоящее сжатое изображение PNG
для теста; в программе сжатия он не участвует.
"""

import os
import random
import struct
import sys
import zlib

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")


def png(width, height, rng):
    """Градиент с шумом -> PNG (deflate внутри, т.е. «изображение в сжатом формате»)."""
    rows = bytearray()
    for y in range(height):
        rows.append(0)  # фильтр строки: none
        for x in range(width):
            noise = rng.randrange(64)
            rows += bytes(((x * 2 + noise) & 255, (y * 2 + noise) & 255, (x + y + noise) & 255))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8 бит, RGB
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b""))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(HERE, exist_ok=True)
    rng = random.Random(19)
    files = {
        "image.png": png(160, 120, rng),
        "repeat.bin": b"A" * 10000,
        "empty.bin": b"",
        "random.bin": bytes(rng.randrange(256) for _ in range(20000)),
        "two_symbols.bin": bytes(rng.choice(b"01") for _ in range(5001)),
    }
    for name, data in files.items():
        with open(os.path.join(HERE, name), "wb") as f:
            f.write(data)
        print(f"{name}: {len(data)} байт")


if __name__ == "__main__":
    main()
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #14 ===
