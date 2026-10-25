# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #12 ===
"""Контейнер ZipMeHuffman (.zmh): заголовок, CRC-32, упаковка битов, диагностики.

Построение кода Хаффмана и декодирование -- в ict/huffman.py.

Формат (все целые -- big-endian):
    смещение  размер  поле
    0         4       сигнатура b"ZMH" + версия формата (1)
    4         8       N -- размер исходных данных, байт
    12        4       CRC-32 исходных данных
    16        8       B -- длина потока кодов, бит
    24        1       способ хранения модели: 0 -- пустая, 1 -- пары, 2 -- битовая карта
    25        ...     модель (длины канонического кода Хаффмана):
                        пары:  m-1 (1 байт), затем m пар (байт, длина)        -> 1 + 2m байт
                        карта: 32 байта -- какие из 256 байтов есть, затем m длин -> 32 + m байт
                      выбирается более короткий вариант (пары при m <= 31)
    ...       4       CRC-32 всех предыдущих байт заголовка
    ...       ceil(B/8)  поток кодов, MSB first; хвост последнего байта -- нулевые биты

Модель -- только длины кодов: канонический код по длинам восстанавливается однозначно.
"""

import struct

from ict.huffman import huffman_lengths, canonical_codes, decode

MAGIC = b"ZMH"
VERSION = 1
FIXED = struct.Struct(">3sBQIQB")  # сигнатура, версия, N, CRC, B, способ хранения модели
MODEL_EMPTY, MODEL_PAIRS, MODEL_BITMAP = 0, 1, 2


class ZmhError(Exception):
    """Базовая ошибка восстановления .zmh."""
    kind = "ошибка"


class ForeignFormat(ZmhError):
    kind = "чужой формат"


class Truncated(ZmhError):
    kind = "файл обрезан"


class Corrupted(ZmhError):
    kind = "файл повреждён"


# --- CRC-32 (полином 0xEDB88320, как в zip/png), табличный, своя реализация ---
_CRC_TABLE = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ 0xEDB88320 if _c & 1 else _c >> 1
    _CRC_TABLE.append(_c)


def crc32(data):
    crc = 0xFFFFFFFF
    table = _CRC_TABLE
    for byte in data:
        crc = (crc >> 8) ^ table[(crc ^ byte) & 0xFF]
    return crc ^ 0xFFFFFFFF


# --- модель ---
def pack_model(lengths):
    """{байт: длина} -> (способ, байты модели). Выбирается более компактный способ."""
    m = len(lengths)
    if m == 0:
        return MODEL_EMPTY, b""
    symbols = sorted(lengths)
    pairs = bytes([m - 1]) + b"".join(bytes([s, lengths[s]]) for s in symbols)
    bitmap = bytearray(32)
    for s in symbols:
        bitmap[s >> 3] |= 0x80 >> (s & 7)
    bitmap = bytes(bitmap) + bytes(lengths[s] for s in symbols)
    return (MODEL_PAIRS, pairs) if len(pairs) <= len(bitmap) else (MODEL_BITMAP, bitmap)


def unpack_model(mode, buf, pos):
    """Читает модель из buf с позиции pos -> ({байт: длина}, новая позиция)."""
    if mode == MODEL_EMPTY:
        return {}, pos
    if mode == MODEL_PAIRS:
        need(buf, pos + 1, "модель")
        m = buf[pos] + 1
        need(buf, pos + 1 + 2 * m, "модель")
        body = buf[pos + 1:pos + 1 + 2 * m]
        symbols = list(body[0::2])
        lens = list(body[1::2])
        if len(set(symbols)) != m:
            raise Corrupted("модель: повторяющиеся символы")
        return dict(zip(symbols, lens)), pos + 1 + 2 * m
    if mode == MODEL_BITMAP:
        need(buf, pos + 32, "модель")
        bitmap = buf[pos:pos + 32]
        symbols = [s for s in range(256) if bitmap[s >> 3] & (0x80 >> (s & 7))]
        need(buf, pos + 32 + len(symbols), "модель")
        lens = buf[pos + 32:pos + 32 + len(symbols)]
        return dict(zip(symbols, lens)), pos + 32 + len(symbols)
    raise Corrupted(f"неизвестный способ хранения модели {mode}")


def need(buf, end, what):
    if len(buf) < end:
        raise Truncated(f"файл обрезан: не хватает байт в части «{what}» ({len(buf)} из {end})")


# --- биты ---
def pack_bits(data, codes):
    """Кодирует data по таблице {байт: (код, длина)} -> (bytes, число бит)."""
    out = bytearray()
    acc = 0      # накопленные биты (младшие nacc бит)
    nacc = 0
    for byte in data:
        code, length = codes[byte]
        acc = (acc << length) | code
        nacc += length
        while nacc >= 8:
            nacc -= 8
            out.append((acc >> nacc) & 0xFF)
        acc &= (1 << nacc) - 1
    total_bits = len(out) * 8 + nacc
    if nacc:  # неполный последний байт: дополняем нулями справа
        out.append((acc << (8 - nacc)) & 0xFF)
    return bytes(out), total_bits


def iter_bits(data, total_bits):
    """Биты потока по одному (MSB first), ровно total_bits штук."""
    produced = 0
    for byte in data:
        for shift in range(7, -1, -1):
            if produced == total_bits:
                return
            yield (byte >> shift) & 1
            produced += 1


# --- сжатие / восстановление ---
def frequencies(data):
    freqs = [0] * 256
    for byte in data:
        freqs[byte] += 1
    return {b: c for b, c in enumerate(freqs) if c}


def build_lengths(freqs):
    """Длины кодов. Один символ -- длина 0: поток пуст, хватает N из заголовка."""
    if len(freqs) <= 1:
        return {b: 0 for b in freqs}
    return huffman_lengths(freqs)


def compress(data):
    """bytes -> (содержимое .zmh, статистика)."""
    freqs = frequencies(data)                  # проход 1: модель
    lengths = build_lengths(freqs)
    if lengths and max(lengths.values()) > 255:
        raise ValueError("длина кода > 255 не помещается в формат")
    codes = canonical_codes(lengths) if len(lengths) > 1 else {}
    if len(lengths) > 1:
        payload, total_bits = pack_bits(data, codes)   # проход 2: кодирование
    else:
        payload, total_bits = b"", 0
    mode, model = pack_model(lengths)
    head = FIXED.pack(MAGIC, VERSION, len(data), crc32(data), total_bits, mode) + model
    header = head + struct.pack(">I", crc32(head))
    stats = {"freqs": freqs, "lengths": lengths, "header": len(header), "data": len(payload),
             "bits": total_bits}
    return header + payload, stats


def decompress(blob):
    """Содержимое .zmh -> исходные bytes. Ошибки: ForeignFormat / Truncated / Corrupted."""
    # 1. Сигнатура: чужой формат или обрезанный в самом начале
    if len(blob) < 4:
        if MAGIC.startswith(blob[:3]) and blob:
            raise Truncated(f"файл обрезан: {len(blob)} байт, заголовок не помещается")
        raise ForeignFormat("нет сигнатуры ZMH: это не файл .zmh")
    if blob[:3] != MAGIC:
        raise ForeignFormat("нет сигнатуры ZMH: это не файл .zmh")
    if blob[3] != VERSION:
        raise ForeignFormat(f"сигнатура ZMH, но неизвестная версия формата {blob[3]}")

    # 2. Заголовок целиком и его контрольная сумма
    need(blob, FIXED.size, "заголовок")
    _, _, n, data_crc, total_bits, mode = FIXED.unpack_from(blob, 0)
    lengths, pos = unpack_model(mode, blob, FIXED.size)
    need(blob, pos + 4, "CRC заголовка")
    (head_crc,) = struct.unpack_from(">I", blob, pos)
    if crc32(blob[:pos]) != head_crc:
        raise Corrupted("повреждён заголовок: CRC-32 заголовка не совпадает")
    start = pos + 4

    # 3. Согласованность модели (заголовок цел, но мог быть записан неверно)
    if n == 0 and lengths:
        raise Corrupted("модель не пуста при нулевом размере данных")
    if n > 0 and not lengths:
        raise Corrupted("пустая модель при ненулевом размере данных")
    if len(lengths) == 1:
        if next(iter(lengths.values())) != 0 or total_bits != 0:
            raise Corrupted("один символ должен иметь длину кода 0 и пустой поток")
    elif lengths:
        if any(l == 0 for l in lengths.values()):
            raise Corrupted("нулевая длина кода при нескольких символах")
        # Неравенство Крафта с равенством: код Хаффмана полный
        if sum(2 ** (max(lengths.values()) - l) for l in lengths.values()) != 2 ** max(lengths.values()):
            raise Corrupted("длины кодов не образуют полный префиксный код (Крафт)")

    # 4. Размер потока
    expected = (total_bits + 7) // 8
    actual = len(blob) - start
    if actual < expected:
        raise Truncated(f"файл обрезан: поток кодов {actual} байт из {expected}")
    if actual > expected:
        raise Corrupted(f"лишние {actual - expected} байт после потока кодов")
    payload = blob[start:]
    if total_bits % 8 and payload[-1] & ((1 << (8 - total_bits % 8)) - 1):
        raise Corrupted("ненулевые биты дополнения в последнем байте")

    # 5. Декодирование
    if len(lengths) <= 1:
        out = bytes([next(iter(lengths))]) * n if lengths else b""
    else:
        bits = iter_bits(payload, total_bits)
        try:
            out = decode(lengths, bits, n)
        except ValueError as e:
            raise Corrupted(f"поток кодов не декодируется: {e}") from None
        if next(bits, None) is not None:
            raise Corrupted("после N символов в потоке остались биты")

    # 6. Целостность результата
    if crc32(out) != data_crc:
        raise Corrupted("CRC-32 восстановленных данных не совпадает с записанным")
    return out
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #12 ===
