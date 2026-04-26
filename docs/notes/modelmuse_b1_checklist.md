# ModelMuse: как открыть B1 (MF6) и проверить входные данные

Этот чеклист относится к этапу **B1** из `README.md` (первая стационарная confined-модель на MODFLOW 6).

## 1) Сначала собери и запусти модель из Python

```bash
python scripts/build_mf6_01_confined.py
```

После успешного запуска проверь, что есть файлы:

- `models/mf6/01_confined_steady/mfsim.nam`
- `models/mf6/01_confined_steady/gwf.nam`
- `models/mf6/01_confined_steady/gwf.dis`
- `models/mf6/01_confined_steady/gwf.ic`
- `models/mf6/01_confined_steady/gwf.npf`
- `models/mf6/01_confined_steady/gwf.chd`
- `models/mf6/01_confined_steady/gwf.oc`
- `models/mf6/01_confined_steady/mf6_01_confined.hds`
- `models/mf6/01_confined_steady/mf6_01_confined.cbc`
- `models/mf6/01_confined_steady/run_summary.txt`

## 2) Как открыть в ModelMuse

> Важно: для MF6 открывай именно **simulation name file** (`mfsim.nam`).

1. Открой ModelMuse.
2. Выбери `File -> Open`.
3. Укажи файл `models/mf6/01_confined_steady/mfsim.nam`.
4. Дождись загрузки всех пакетов (`TDIS`, `IMS`, `DIS`, `IC`, `NPF`, `CHD`, `OC`).

Если ModelMuse предлагает выбрать тип модели, выбирай **MODFLOW 6**.

## 3) Чеклист входных данных в ModelMuse (B1)

Проверь пункты ровно в этом порядке.

### A. Сетка и геометрия

- `nlay = 1`, `nrow = 10`, `ncol = 10`.
- Размер ячейки: `delr = 100`, `delc = 100` (равномерная сетка).
- `top = 10`, `botm = 0`.
- Модель confined (в `NPF` используется `icelltype = 0`).

### B. Временная схема

- `nper = 1`.
- Один steady-state период (`PERLEN = 1.0`, `NSTP = 1`, `TSMULT = 1.0`).

### C. Параметры фильтрации и старт

- `K = 10` (однородно во всех ячейках).
- Начальный напор (`IC`) = `5`.

### D. Граничные условия

- Слева (`col = 1`): `CHD = 10` для всех строк.
- Справа (`col = 10`): `CHD = 0` для всех строк.
- Верх/низ по рядам и границы, где нет CHD, — no-flow (по умолчанию).

### E. Вывод

- В `OC` включено сохранение `HEAD` и `BUDGET` для `ALL`.
- Должны формироваться `.hds` и `.cbc`.

## 4) Быстрая проверка результатов после открытия

1. Построй карту напоров в ModelMuse или открой `heads_map.png`.
2. Убедись, что напор убывает почти линейно слева направо (от ~10 к ~0).
3. Открой `run_summary.txt` и проверь:
   - `Head left boundary mean` близко к `10`;
   - `Head right boundary mean` близко к `0`;
   - `Budget percent discrepancy (%)` близок к `0`.

## 5) Типовые причины несоответствий

- Открыт не `mfsim.nam`, а отдельный пакетный файл.
- Выбран не MF6-проект при открытии.
- Изменены единицы/сетка при импорте.
- Ручная правка `gwf.chd` с нарушением левой/правой границы.
