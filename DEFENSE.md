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
