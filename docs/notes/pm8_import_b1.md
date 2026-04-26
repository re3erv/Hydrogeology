# PM8: как открыть B1-модель из FloPy/MODFLOW-2005

Если в **Processing Modflow 8** диалог `File -> Open` просит только `*.pm5`, это нормально:

- `*.pm5` — это **внутренний формат проекта PMWIN/PM8**;
- FloPy/MODFLOW-2005 пишет **native MODFLOW** (`*.nam`, `*.dis`, `*.bas`, ...).

## Правильный путь импорта

1. Запусти скрипт B1:
   ```bash
   python scripts/build_mf2005_01_confined.py
   ```
2. В PM8 выбери пункт меню импорта/конвертации native MODFLOW модели (обычно это `Import` или `Convert` для MODFLOW Name File, а не обычный `Open`).
3. Укажи файл:
   `models/mf2005/01_confined_steady/mf2005_01_confined.nam`.
4. После импорта PM8 создаст свой проект `*.pm5` — его уже можно открывать через `File -> Open`.

## Что проверить после импорта

- геометрия сетки 1x10x10;
- constant head слева 10, справа 0;
- линейный градиент heads;
- budget discrepancy в `.list` близка к нулю.

## Если PM8 пишет `Failed to convert the selected model`

Проверьте в таком порядке:

1. Используйте короткий ASCII-путь без пробелов/кириллицы, например `C:/gw/b1`.
   Повторно соберите модель:
   ```bash
   python scripts/build_mf2005_01_confined.py --workspace C:/gw/b1
   ```
   И импортируйте `C:/gw/b1/mf2005_01_confined.nam`.
2. Убедитесь, что выбираете именно режим `MODFLOW-2000/2005` (вы выбрали верно).
3. Оставьте `Refinement factor for rows/columns = 1` для базовой проверки.
4. Если ошибка повторяется, проверьте в папке модели, что есть файлы `*.dis`, `*.bas`, `*.lpf`, `*.pcg`, `*.oc` и `*.nam` (файл `.cbc` в PM8-compat режиме может отсутствовать).
- Если в `ConvertLog.txt` ошибка именно `Discretization file --- ERROR`, пересоберите модель последней версией скрипта: он теперь пишет `DIS` с явными массивами (`DELR/DELC/TOP/BOTM`) и явными `ITMUNI/LENUNI`, что обычно стабильнее для PM8-конвертера.

В этой версии скрипта BAS пишется в fixed format (`ifrefm=False`), а OC в не-compact режиме (`compact=False`) для лучшей совместимости с legacy-конвертером PM8.


## Fallback для ошибки DIS

Скрипт автоматически создаёт fallback-наборы `.nam` с упрощёнными `DIS`-вариантами:
- `mf2005_01_confined_pm8.nam`;
- `mf2005_01_confined_pm8_u0.nam` (с `ITMUNI/LENUNI = 0/0`);
- `mf2005_01_confined_pm8_tr.nam` (с `TR` в последней строке периода);
- `mf2005_01_confined_pm8_num0.nam` (с числовым флагом `0` вместо `SS/TR`);
- `mf2005_01_confined_pm8_num1.nam` (с числовым флагом `1` вместо `SS/TR`);
- `mf2005_01_confined_pm8_full.nam` (полные массивы DIS через `INTERNAL ... (FREE)`).

Если обычный `mf2005_01_confined.nam` снова даёт `Discretization file --- ERROR`, импортируйте fallback-файлы в этом порядке: `pm8` -> `pm8_u0` -> `pm8_tr` -> `pm8_num0` -> `pm8_num1` -> `pm8_full`.
