# Ядро задачи 1.3: код Хаффмана. Контейнер, биты и CRC -- в ict/zmh.py.
# Контракт функций (заготовка сигнатур: Claude, SOURCES.md #13; тела -- TODO).


def huffman_lengths(freqs):
    """{байт: частота} (не меньше двух символов) -> {байт: длина кода Хаффмана}."""
    raise NotImplementedError


def canonical_codes(lengths):
    """{байт: длина} -> {байт: (код как целое, длина)} -- канонический код."""
    raise NotImplementedError


def decode(lengths, bits, n):
    """Декодирует ровно n байт из итератора битов (0/1) по длинам канонического кода.
    Если биты кончились раньше или встретился несуществующий код -- raise ValueError."""
    raise NotImplementedError
