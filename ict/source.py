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
    """Загружает и проверяет описание источника любого типа. Ошибка -> SourceError."""
    return parse_source(read_json(path))


# ---------------------------------------------------------------------------
# Расширенный формат (см. FORMAT_SPEC.md). Поле "type" выбирает вид источника;
# без него описание -- исходного формата ("switching"), поэтому старые файлы
# читаются без изменений. Каждый парсер возвращает словарь с ключами
# "type" и "alphabet" плюс поля своего типа:
#   switching: models, switches, source            (как раньше)
#   markov:    order d, initial {состояние: p}, transitions {состояние: {символ: p}},
#              где состояние -- кортеж из d символов
#   mixture:   components [(вес Fraction, источник), ...]
# ---------------------------------------------------------------------------

TYPES = ("switching", "markov", "mixture")
COMMON_KEYS = ("type", "description")  # допустимы в описании любого типа


def parse_source(data, where=""):
    """Разобранный JSON-объект -> нормализованное описание источника.
    where -- префикс пути для сообщений об ошибках во вложенных описаниях."""
    if not isinstance(data, dict):
        raise SourceError(f"{where or 'описание'}: ожидается объект")
    kind = data.get("type", "switching")
    if "description" in data and not isinstance(data["description"], str):
        raise SourceError(f"{where}description: ожидается строка")
    if kind == "switching":
        return _parse_switching(data, where)
    if kind == "markov":
        return _parse_markov(data, where)
    if kind == "mixture":
        return _parse_mixture(data, where)
    raise SourceError(f"{where}type: неизвестный тип {kind!r}, допустимы {list(TYPES)}")


def _check_keys(data, required, where):
    for key in required:
        if key not in data:
            raise SourceError(f"{where}нет обязательного ключа {key!r}")
    extra = set(data) - set(required) - set(COMMON_KEYS)
    if extra:
        # Ловит опечатки вроде "sources" вместо "source".
        raise SourceError(f"{where}неизвестные ключи: {sorted(extra)}")


def _add_symbols(alphabet, symbols):
    """Дописывает новые символы в алфавит в порядке первого появления
    (детерминированно, не зависит от порядка обхода set)."""
    for symbol in symbols:
        if symbol not in alphabet:
            alphabet.append(symbol)


def _parse_switching(data, where):
    _check_keys(data, TOP_KEYS, where)

    if not isinstance(data["models"], dict) or not data["models"]:
        raise SourceError(f"{where}models: ожидается непустой объект")
    models = {name: parse_distribution(dist, f"{where}models.{name}")
              for name, dist in data["models"].items()}

    if not isinstance(data["switches"], dict) or not data["switches"]:
        raise SourceError(f"{where}switches: ожидается непустой объект")
    switches = {}
    for name, dist in data["switches"].items():
        switches[name] = parse_distribution(dist, f"{where}switches.{name}")
        for model in switches[name]:
            if model not in models:
                raise SourceError(f"{where}switches.{name}: несуществующая модель {model!r}")

    source = data["source"]
    if not isinstance(source, list) or not source:
        raise SourceError(f"{where}source: ожидается непустой список переключателей")
    for i, name in enumerate(source):
        if not isinstance(name, str) or name not in switches:
            raise SourceError(f"{where}source[{i}]: несуществующий переключатель {name!r}")

    alphabet = []
    for dist in models.values():
        _add_symbols(alphabet, dist)

    return {"type": "switching", "models": models, "switches": switches,
            "source": list(source), "alphabet": alphabet}


def _parse_state(key, d, where):
    """Ключ "a b" -> кортеж ("a", "b"); длина должна равняться порядку d."""
    state = tuple(key.split())
    if len(state) != d:
        raise SourceError(f"{where}: состояние {key!r} должно состоять из {d} символов через пробел")
    return state


def _parse_markov(data, where):
    _check_keys(data, ("type", "order", "initial", "transitions"), where)

    d = data["order"]
    if not isinstance(d, int) or isinstance(d, bool) or d < 1:
        raise SourceError(f"{where}order: ожидается целое число >= 1, получено {d!r}")

    if not isinstance(data["transitions"], dict) or not data["transitions"]:
        raise SourceError(f"{where}transitions: ожидается непустой объект")
    transitions = {}
    for key, dist in data["transitions"].items():
        state = _parse_state(key, d, f"{where}transitions")
        if state in transitions:
            raise SourceError(f"{where}transitions: состояние {key!r} задано дважды")
        transitions[state] = parse_distribution(dist, f"{where}transitions.{key}")
        for symbol in transitions[state]:
            if not symbol or symbol != symbol.strip() or len(symbol.split()) != 1:
                raise SourceError(f"{where}transitions.{key}: символ {symbol!r} пуст или содержит пробел")

    raw_initial = parse_distribution(data["initial"], f"{where}initial")
    initial = {}
    for key, p in raw_initial.items():
        state = _parse_state(key, d, f"{where}initial")
        if state in initial:
            raise SourceError(f"{where}initial: состояние {key!r} задано дважды")
        initial[state] = p

    # Каждое состояние, в которое процесс может попасть, обязано иметь строку
    # переходов -- иначе генерация "застрянет". Обход в ширину от начальных состояний.
    reached = [s for s, p in initial.items() if p > 0]
    seen = set(reached)
    while reached:
        state = reached.pop()
        if state not in transitions:
            raise SourceError(f"{where}transitions: нет строки для достижимого состояния {' '.join(state)!r}")
        for symbol, p in transitions[state].items():
            nxt = state[1:] + (symbol,)
            if p > 0 and nxt not in seen:
                seen.add(nxt)
                reached.append(nxt)

    alphabet = []
    for state in initial:
        _add_symbols(alphabet, state)
    for state, dist in transitions.items():
        _add_symbols(alphabet, state)
        _add_symbols(alphabet, dist)

    return {"type": "markov", "order": d, "initial": initial,
            "transitions": transitions, "alphabet": alphabet}


def _parse_mixture(data, where):
    _check_keys(data, ("type", "components"), where)

    comps = data["components"]
    if not isinstance(comps, list) or not comps:
        raise SourceError(f"{where}components: ожидается непустой список")
    components = []
    alphabet = []
    for i, item in enumerate(comps):
        w = f"{where}components[{i}]"
        if not isinstance(item, dict) or set(item) != {"weight", "source"}:
            raise SourceError(f"{w}: ожидается объект ровно с ключами 'weight' и 'source'")
        weight = parse_prob(item["weight"], f"{w}.weight")
        comp = parse_source(item["source"], f"{w}.source.")
        components.append((weight, comp))
        _add_symbols(alphabet, comp["alphabet"])

    total = sum(weight for weight, _ in components)
    if total != 1:
        raise SourceError(f"{where}components: веса не нормированы, сумма = {total}")

    return {"type": "mixture", "components": components, "alphabet": alphabet}
# === END GENERATED: Claude Opus 5.5 (Anthropic), see SOURCES.md #1 ===
