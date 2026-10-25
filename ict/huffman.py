# Ядро задачи 1.3: код Хаффмана. Контейнер, биты и CRC -- в ict/zmh.py.
# Контракт функций (заготовка сигнатур: Claude, SOURCES.md #13; тела -- TODO).

import heapq

def huffman_lengths(freqs):
    """{байт: частота} (не меньше двух символов) -> {байт: длина кода Хаффмана}."""
    if len(freqs)<2:
        raise ValueError("для кода хаффмана нужно не менее двух символво")
    heap = [(w, i, [s]) for i, (s, w) in enumerate(sorted(freqs.items()))]
    heapq.heapify(heap)
    lenghts = dict.fromkeys(freqs, 0)
    counter = len(heap)
    while len(heap)> 1:
        w1, _, left = heapq.heappop(heap)
        w2, _, right = heapq.heappop(heap)
        merged = left + right
        for s in merged:
            lenghts[s] += 1

        heapq.heappush(heap, (w1+w2, counter, merged))
        counter += 1
    return lenghts


def canonical_codes(lengths):
    """{байт: длина} -> {байт: (код как целое, длина)} -- канонический код."""
    codes = {}
    code = 0
    prev_len = 0
    for s in sorted(lengths, key=lambda s: (lengths[s], s)):
        length = lengths[s] 
        code <<= length - prev_len # ооох кажется пришло время
        codes[s] = (code, length)
        code += 1
        prev_len = length
    return codes

def decode(lengths, bits, n):
    """Декодирует ровно n байт из итератора битов (0/1) по длинам канонического кода.
    Если биты кончились раньше или встретился несуществующий код -- raise ValueError."""
    if any(l <= 0 for l in lengths.values()):
        raise ValueError("длина кода должна быть положительной")
    
    order = sorted(lengths, key=lambda s: (lengths[s], s))
    max_len = lengths[order[-1]]
    count = [0] * (max_len + 1)
    for s in order:
        count[lengths[s]] += 1
    first = [0] * (max_len + 1)
    index = [0] * (max_len + 1)
    code = idx = 0
    for length in range(1, max_len + 1):
        code = (code + count[length - 1]) << 1
        first[length] = code
        index[length] = idx
        idx += count[length]

    out = bytearray()
    for _ in range(n):
        code = 0
        for length in range(1, max_len + 1):
            bit = next(bits, None)
            if bit is None:
                raise ValueError(f"биты кончились на символе {len(out) + 1} из {n}")
            code = (code << 1) | bit
            k = code - first[length]
            if 0 <= k < count[length]:
                out.append(order[index[length] + k])
                break
        else:
            raise ValueError(f"несуществующий код на символе {len(out) + 1}")
    return bytes(out)
