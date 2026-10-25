# === BEGIN GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #1 ===
"""Загрузка и проверка описания дискретного источника (задача 1.1).

Результат load_source() -- словарь:
    {
        "models":   {имя модели: {символ: Fraction}},
        "switches": {имя переключателя: {имя модели: Fraction}},
        "source":   [имя переключателя, ...],
        "alphabet": [символ, ...],   # объединение символов всех моделей
    }
Все вероятности -- точные дроби Fraction, float не используется нигде.
"""

import json
from fractions import Fraction

TOP_KEYS = ("models", "switches", "source")


class SourceError(Exception):
    """Некорректное описание источника."""


def parse_prob(value, where):
    """Строка с вероятностью -> Fraction. where -- место в файле для сообщения."""
    # По формату вероятность -- строка. Число в JSON отвергаем: float
    # уже потерял точность ("0.1" как float != 1/10).
    if not isinstance(value, str):
        raise SourceError(f"{where}: вероятность должна быть строкой, получено {value!r}")
    # В PDF задания дроби набраны символом U+2215 вместо обычного "/".
    text = value.replace("∕", "/").strip()
    try:
        p = Fraction(text)  # понимает "1/3", "0.3" (= 3/10 точно), "1e-3"
    except (ValueError, ZeroDivisionError):  # "abc" и "1/0" соответственно
        raise SourceError(f"{where}: не удалось разобрать вероятность {value!r}") from None
    if p < 0:
        raise SourceError(f"{where}: отрицательная вероятность {value}")
    return p


def parse_distribution(obj, where):
    """JSON-объект {исход: "вероятность"} -> {исход: Fraction}, сумма ровно 1."""
    if not isinstance(obj, dict) or not obj:
        raise SourceError(f"{where}: ожидается непустой объект {{исход: вероятность}}")
    dist = {name: parse_prob(value, f"{where}.{name}") for name, value in obj.items()}
    total = sum(dist.values())
    if total != 1:
        raise SourceError(f"{where}: распределение не нормировано, сумма = {total}")
    return dist


def _reject_duplicates(pairs):
    """Хук для json: обычный json молча оставляет последний из повторных ключей."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise SourceError(f"повторяющийся ключ {key!r}")
        result[key] = value
    return result


def read_json(path):
    """Читает JSON-файл, превращая любые проблемы чтения в SourceError."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f, object_pairs_hook=_reject_duplicates)
    except OSError as e:
        raise SourceError(f"не удалось открыть файл {path}: {e.strerror}") from None
    except UnicodeDecodeError:
        raise SourceError(f"{path}: файл не в кодировке UTF-8") from None
    except json.JSONDecodeError as e:
        raise SourceError(f"{path}: некорректный JSON, строка {e.lineno}, столбец {e.colno}: {e.msg}") from None


def load_source(path):
    """Загружает и проверяет описание источника. Ошибка -> SourceError."""
    data = read_json(path)
    if not isinstance(data, dict):
        raise SourceError("верхний уровень описания должен быть объектом")
    for key in TOP_KEYS:
        if key not in data:
            raise SourceError(f"нет обязательного ключа {key!r}")
    extra = set(data) - set(TOP_KEYS)
    if extra:
        # Ловит опечатки вроде "sources" вместо "source".
        raise SourceError(f"неизвестные ключи верхнего уровня: {sorted(extra)}")

    if not isinstance(data["models"], dict) or not data["models"]:
        raise SourceError("models: ожидается непустой объект")
    models = {name: parse_distribution(dist, f"models.{name}")
              for name, dist in data["models"].items()}

    if not isinstance(data["switches"], dict) or not data["switches"]:
        raise SourceError("switches: ожидается непустой объект")
    switches = {}
    for name, dist in data["switches"].items():
        switches[name] = parse_distribution(dist, f"switches.{name}")
        for model in switches[name]:
            if model not in models:
                raise SourceError(f"switches.{name}: несуществующая модель {model!r}")

    source = data["source"]
    if not isinstance(source, list) or not source:
        raise SourceError("source: ожидается непустой список переключателей")
    for i, name in enumerate(source):
        if not isinstance(name, str) or name not in switches:
            raise SourceError(f"source[{i}]: несуществующий переключатель {name!r}")

    # Алфавит в порядке первого появления -- детерминированный, не зависит от set.
    alphabet = []
    for dist in models.values():
        for symbol in dist:
            if symbol not in alphabet:
                alphabet.append(symbol)

    return {"models": models, "switches": switches, "source": list(source), "alphabet": alphabet}
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #1 ===
