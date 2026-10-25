# Шпаргалка команд для защиты

Все команды запускаются из корня репозитория. Python 3.11+, внешних зависимостей нет.
Коды возврата: `0` — успех, `2` — некорректный вход (сообщение в stderr), `1` — внутренняя ошибка, `130` — прервано Ctrl+C.
Узнать код возврата последней команды: PowerShell — `$LASTEXITCODE`, bash — `echo $?`.

## Общее

```bash
python run.py --help                      # список режимов
python run.py generate --help             # ключи конкретного режима
python run.py --variant                   # вариант s = 19 и параметры k, M, L, d, q, eps
python run.py --s 7 --variant             # параметры для любого другого s (ключ --s пишется ДО режима)
```

## Задача 1.1, режим 1 — реализация источника

```bash
python run.py generate tests/sources/example2.json --n 40                 # 40 символов, seed по умолчанию 0
python run.py generate tests/sources/example2.json --n 40 --seed 42       # другой seed -> другая реализация
python run.py generate tests/sources/example2.json --n 40 --seed 42       # тот же seed -> побитово то же самое
python run.py generate tests/sources/example2.json --n None               # бесконечно; остановка -- Ctrl+C
python run.py generate tests/sources/example2.json --n 0                  # N <= 0 -- тоже бесконечно (по условию)
python run.py generate tests/sources/var_stationary.json --n 60           # пример варианта: стационарный
python run.py generate tests/sources/var_nonstationary.json --n 60        # нестационарный (период 7)
python run.py generate tests/sources/var_markov.json --n 60               # марковский d=2: видны серии
python run.py generate tests/sources/var_markov_nonstationary.json --n 20 # всегда начинается с "a a"
python run.py generate tests/sources/var_mixture.json --n 60 --seed 1     # смесь: одна компонента на всю реализацию
python run.py generate tests/sources/var_mixture.json --n 60 --seed 5     # другой seed -- другая компонента
python run.py generate tests/sources/degenerate/multichar_symbols.json --n 10   # многобуквенные символы -> через пробел
```

## Задача 1.1, режим 2 — точная вероятность и частотная оценка

```bash
python run.py prob tests/sources/example2.json --n 1000 --seq 0 0 --seed 1          # 17/60, 527/1800, таблица
python run.py prob tests/sources/example2.json --n 1000 --seq 0 1 1                  # блок длины 3
python run.py prob tests/sources/var_nonstationary.json --n 1000 --seq a b           # частота -> среднее по периоду
python run.py prob tests/sources/var_markov.json --n 1000 --seq a a                   # стационарный: (1) = (2) = 1/8
python run.py prob tests/sources/var_markov_nonstationary.json --n 1000 --seq a a     # (1) = 1, а частота -> 1/8
python run.py prob tests/sources/var_mixture.json --n 1000 --seq a a --seed 1         # частота -> 0.19, а не 0.108
python run.py prob tests/sources/degenerate/deterministic_period.json --n 100 --seq a b   # (1) = 1, (2) = 1/2
```

Ожидаемое для первой команды (числа из отчёта):
```
1) Pr{X1..Xr = a1..ar}           = 17/60  ~ 0.283333
2) среднее по сдвигам в периоде    = 527/1800  ~ 0.292778
...
 1000000    0.292832    0.009499    0.000055
```

### Ручная задача №4 (пример 2, такт L+2, блок длины 2 с первого такта)

Такт L+2 = 6 — это индекс 5 с нуля, переключатель `source[5 mod 4] = source[1] = switch_2`, распределение P(0) = 17/30, P(1) = 13/30.
Блок с первого такта:
```bash
python run.py prob tests/sources/example2.json --n 10 --seq 0 1     # строка 1): Pr{X1=0, X2=1} = 1/2 * 13/30 = 13/60
```

## Задача 1.2 — равномерное кодирование источника без памяти

```bash
python run.py entropy tests/sources/var_stationary.json        # стационарен, без памяти: P и H = 1.962031
python run.py entropy tests/sources/var_nonstationary.json     # нарушено: распределение на такте 2 != такт 0
python run.py entropy tests/sources/var_markov.json            # нарушено: память
python run.py entropy tests/sources/var_mixture.json           # нарушено: смесь (зависимость через компоненту)
python run.py entropy tests/sources/degenerate/one_symbol.json # H = 0
python run.py code tests/sources/var_stationary.json --rate 2.5             # R > H: минимальное n = 4, n0 существует
python run.py code tests/sources/var_stationary.json --rate 1.9 --nmax 12   # R < H: n0 не существует
python run.py code tests/sources/task12/five_symbols.json --rate 2          # k = 5, n_max = 50: время < 10 с
python run.py code tests/sources/task12/binary.json --rate 2/3 --q 2 --nmax 3 --eps 1/10 --out out/bin.json   # ручная задача 3
python run.py code tests/sources/var_stationary.json --rate 2.5 --q 3 --eps 1/100   # q и eps можно переопределить
python run.py code tests/sources/var_mixture.json --rate 1                  # ошибка: не источник без памяти
python run.py code tests/sources/var_stationary.json --rate -1              # ошибка: R < 0
```

По умолчанию `q` и `eps` берутся из варианта (q = 7, eps = 1/1000), `--nmax 50`, код пишется в `out/code.json`.
Для малых кодов (≤ 256 слов) в файле перечислены сами пары «блок → кодовое слово».

Ручная задача 3 (двоичный, P(0) = 3/4, n = 3): типы 000 (1 блок, 27/64), 001 (3 блока по 9/64), 011 (3 блока по 3/64), 111 (1 блок, 1/64).
4 наиболее вероятных блока = 000 + три блока типа «одна единица»: 27/64 + 27/64 = 54/64, Pe = 10/64 = 0.15625.

## Задача 1.3 — архиватор ZipMeHuffman

```bash
python run.py compress tests/files/ru.txt --stats                 # -> tests/files/ru.txt.zmh, H, l_avg, заголовок, данные, коэффициент
python run.py decompress tests/files/ru.txt.zmh                   # исходник есть -> пишет ru.restored.txt, проверяет CRC
python run.py compress tests/files/repeat.bin --stats             # один байт: длина кода 0, заголовок 32 байта, данных 0
python run.py compress tests/files/empty.bin --stats              # пустой: 29 байт заголовка
python run.py compress tests/files/image.png --stats              # сжатый PNG: H ~ 8, файл вырастает
python run.py compress FILE --out other.zmh                       # своё имя результата
python run.py decompress other.zmh --out restored.bin             # своё имя восстановленного
python tests/run_tests.py                                         # все тесты + перегенерация RESULTS.md (~35 с)
```

Проверка ручных задач 2 и 6 (веса — целые, дроби или десятичные):
```bash
python run.py huffman 5 3 2 1 1 1            # длины, канонические слова, l_avg, H, Крафт, заголовок .zmh, граница «сжатия в минус»
python run.py huffman 1/2 1/4 1/8 1/8        # степени двойки: l_avg = H
python run.py decompress tests/zmh/ru.txt.zmh --out out/ru_check.txt   # готовый .zmh из репозитория
```

Диагностики (`tests/zmh/broken_*.zmh` создаёт `tests/run_tests.py`):
```bash
python run.py decompress tests/zmh/broken_foreign.zmh       # PNG вместо zmh       -> "чужой формат", код 3
python run.py decompress tests/zmh/broken_trunc_data.zmh    # отрезаны 100 байт    -> "файл обрезан", код 4
python run.py decompress tests/zmh/broken_flip_data.zmh     # инверсия бита в данных -> "файл повреждён", код 5
python run.py decompress tests/zmh/broken_flip_header.zmh   # инверсия бита в заголовке -> CRC заголовка, код 5
```

Заголовок `.zmh` (big-endian): `ZMH` + версия (4) | N (8) | CRC-32 данных (4) | B — бит в потоке (8) | способ модели (1) | модель | CRC-32 заголовка (4).
Фиксированная часть — 29 байт. Модель — длины канонического кода: пары `(байт, длина)` → 1 + 2m байт, или битовая карта → 32 + m байт (берётся меньшее, пары при m ≤ 31).
Пример: m = 1 → 29 + 3 = 32 байта; m = 2 → 34; m = 256 → 29 + 288 = 317.

## Некорректные и вырожденные входы (закрытый тест)

```bash
python run.py generate tests/sources/bad/not_normalized.json --n 5        # распределение не нормировано
python run.py generate tests/sources/bad/negative_prob.json --n 5         # отрицательная вероятность
python run.py generate tests/sources/bad/unknown_model.json --n 5         # несуществующая модель
python run.py generate tests/sources/bad/unknown_switch.json --n 5        # несуществующий переключатель
python run.py generate tests/sources/bad/empty_source.json --n 5          # пустой source
python run.py generate tests/sources/bad/broken_json.json --n 5           # битый JSON (строка и столбец)
python run.py generate tests/sources/bad/duplicate_key.json --n 5         # повторяющийся ключ
python run.py generate tests/sources/bad/not_utf8.json --n 5              # не UTF-8
python run.py generate tests/sources/bad/mixture_nested_error.json --n 5  # ошибка во вложенном описании -- с путём
python run.py generate nonexistent.json --n 5                             # нет файла
python run.py generate tests/sources/example2.json --n abc                # N не число
python run.py prob tests/sources/example2.json --n 0 --seq 0              # N = 0 в режиме 2
python run.py prob tests/sources/example2.json --n 2 --seq 0 0 1          # блок длиннее N
python run.py prob tests/sources/example2.json --n 50 --seq 0 x           # символ не из алфавита -> вероятность 0
python run.py generate tests/sources/degenerate/one_symbol.json --n 10    # один символ
python run.py generate tests/sources/degenerate/unicode_slash.json --n 10 # дроби с "∕" из PDF
```

Проверить все битые файлы разом (PowerShell):
```powershell
Get-ChildItem tests/sources/bad/*.json | ForEach-Object { "{0,-32} {1}" -f $_.Name, (python run.py generate $_.FullName --n 5 2>&1 | Select-Object -First 1) }
```

## Где что в коде («покажи в своём коде, где…»)

| что | где |
|---|---|
| параметры варианта | `ict/variant.py`, `get_params` |
| вероятность — строка → `Fraction`, отказ от float | `ict/source.py`, `parse_prob` |
| проверка нормировки | `ict/source.py`, `parse_distribution` |
| разбор расширенного формата | `ict/source.py`, `parse_source`, `_parse_markov`, `_parse_mixture` |
| точный случайный выбор без float | `ict/task11.py`, `sample` |
| такт i → переключатель i mod L | `ict/task11.py`, `switching_generate` |
| смесь выбирает компоненту один раз | `ict/task11.py`, `mixture_generate` |
| распределение символа на такте | `ict/task11.py`, `symbol_dist` |
| точная вероятность блока | `ict/task11.py`, `block_prob` и `*_block_prob` |
| среднее по периоду | `ict/task11.py`, `avg_block_prob`, `period` |
| частотная оценка, знаменатель N−r+1 | `ict/task11.py`, `freq_estimates` |
| seed → `random.Random` | `run.py`, `cmd_generate` / `cmd_prob` |
| проверка «стационарен и без памяти» | `ict/task12.py`, `check_memoryless` |
| энтропия | `ict/task12.py`, `entropy` |
| ℓ(n) без float | `ict/task12.py`, `code_length` |
| типы блоков, мультиномиальный коэффициент, целочисленные веса | `ict/task12.py`, `best_types` |
| таблица Pe(n), вывод о n0 | `run.py`, `cmd_code` |
| длины кодов Хаффмана | `ict/huffman.py`, `huffman_lengths` |
| канонический код | `ict/huffman.py`, `canonical_codes` |
| декодирование | `ict/huffman.py`, `decode` |
| первый проход (модель) / второй (кодирование) | `ict/zmh.py`, `compress`: `frequencies` → `pack_bits` |
| неполный последний байт | `ict/zmh.py`, `pack_bits` (дополнение нулями) и `decompress` (B бит, проверка дополнения) |
| хранение модели | `ict/zmh.py`, `pack_model` / `unpack_model` |
| CRC-32 | `ict/zmh.py`, `crc32` |
| чужой / обрезан / повреждён | `ict/zmh.py`, `decompress`, классы `ForeignFormat` / `Truncated` / `Corrupted` |

## Сценарии защиты (12 минут)

### Закрытый тест (3 мин): что могут дать и что должно произойти

| что дали | команда | ожидаемое поведение |
|---|---|---|
| свой JSON исходного формата | `generate F --n 30`, `prob F --n 1000 --seq …` | работает без конвертации; дроби, десятичные, «∕» из PDF, BOM из Блокнота — принимаются |
| распределение с суммой ≠ 1 | `generate F --n 5` | «не нормировано», код 2 |
| ссылка на несуществующую модель/переключатель, пустой `source`, отрицательная вероятность | `generate F --n 5` | сообщение с указанием места, код 2 |
| вероятность числом, а не строкой (`0.5`) | `generate F --n 5` | отказ: float теряет точность, код 2 |
| блок с символом не из алфавита | `prob F --n 100 --seq a z` | вероятности 0, частота 0 — не ошибка |
| блок длиннее N | `prob F --n 2 --seq a b c` | код 2 |
| источник с памятью/нестационарный в 1.2 | `entropy F` | называет нарушенное условие |
| R < H, R = H, R > log₂k | `code F --rate …` | n₀ нет (с оговоркой о малых n) / есть / Pₑ = 0 с малого n |
| свой файл для архиватора | `compress F --stats`, затем `decompress F.zmh` | пишет `F.restored.ext`, «CRC-32 совпадает» |
| пустой файл, файл из одного байта | `compress` | 29 байт / 32 байта, восстановление корректно |
| PNG/ZIP/JPG | `compress --stats` | файл вырастает на ~317 байт: H ≈ 8 |
| испорченный .zmh | `decompress` | чужой формат — 3, обрезан — 4, повреждён — 5 |
| каталог вместо файла, нет файла | любая команда | «не удалось прочитать», код 2 |

Если что-то упало с кодом 1 («внутренняя ошибка») — сказать честно, показать, что трейсбека нет, и объяснить, где ловится.

### Ручной счёт (4 мин): чем сверять

| задача | сверка программой |
|---|---|
| 1. энтропия 3 символов | `python run.py huffman 1/2 1/3 1/6` → строка «энтропия H» |
| 2. Хаффман для 6 весов | `python run.py huffman w1 … w6` → длины, l_avg, H |
| 3. двоичный, n = 3, 4 блока | `code tests/sources/task12/binary.json --rate 2/3 --q 2 --nmax 3` (P подменить в JSON) |
| 4. пример 2, такт L+2 | `prob tests/sources/example2.json --n 10 --seq x y` → строка 1) |
| 5. граница по R | `entropy F` → H; граница R = H |
| 6. заголовок .zmh по частотам | `python run.py huffman c1 … cm` → «заголовок .zmh», «сжатие в минус при N < …» |

### Модификация на месте (2 мин): типовые изменения и правильные предсказания

| изменение | предсказание |
|---|---|
| другой `--seed` | реализация и частоты меняются; точные Pr₁ и среднее — нет |
| в `source` все элементы одинаковые | Pr₁ = среднее по периоду; `entropy` перестаёт ругаться |
| циклически сдвинуть `source` | Pr₁ меняется, среднее по периоду — нет (та же сумма по сдвигам); произвольная перестановка при r ≥ 2 меняет и среднее |
| в `mixture` веса 1 и 0 | источник становится эргодичным: частота → вероятность единственной компоненты |
| в `markov` все переходы и `initial` равномерные | источник без памяти, равномерный; вероятность любого блока = k⁻ʳ |
| увеличить ε | минимальное n уменьшается или появляется |
| q = 2 вместо 7 | ℓ(n) = ⌊nR⌋, шаг по скорости мельче, Pₑ(n) ведёт себя ровнее |
| `⌊ ⌋` → `⌈ ⌉` в `code_length` | ℓ больше на 1 для части n, реальная скорость > R, Pₑ меньше |
| `<` вместо `<=` в `code_length` | различие только когда q^{ℓb} = 2^{na} точно (например q = 2, nR — целое): ℓ на 1 меньше |
| порядок ничьих в `huffman_lengths` | слова и, возможно, длины меняются, l_avg — нет |
| хранить модель всегда парами | заголовок при m > 31 растёт: при 256 байтах 29 + 513 = 542 вместо 317 |
| убрать проверку CRC данных | инверсия бита в данных обычно всё равно ловится декодером (лишние/недостающие биты), но часть порч пройдёт молча |
| инвертировать 1 бит в середине данных .zmh | «файл повреждён», код 5 (CRC данных или декодирование) |
| дописать байт в конец .zmh | «повреждён: лишние байты», код 5 |
