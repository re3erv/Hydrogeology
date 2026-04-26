# Hydrogeology

Учебный репозиторий по FloPy с фокусом **только на MODFLOW 6 (MF6)**.

Дата обновления: 2026-04-26.

## Важное изменение курса

С этого момента в проекте **не используется MODFLOW-2005 и Processing Modflow 8**.
Причина: нестабильная/неподходящая интеграция с PM8 в текущем учебном процессе.

Остаётся единый стек:

- Python
- FloPy
- MODFLOW 6
- matplotlib/pandas для анализа и визуализации

## Быстрый старт

1. Создать окружение:

```bash
conda env create -f environment.yml
conda activate modflow-learning
```

2. Проверить окружение и исполняемый файл MF6:

```bash
python scripts/check_environment.py --diagnose-only
```

3. Запустить первую стационарную confined-модель (этап B1):

```bash
python scripts/build_mf6_01_confined.py
```


4. Открыть проект в ModelMuse и проверить входные данные по чеклисту:

```text
docs/notes/modelmuse_b1_checklist.md
```

Ожидаемые артефакты:

- `models/mf6/01_confined_steady/mfsim.nam`
- `models/mf6/01_confined_steady/mf6_01_confined.hds`
- `models/mf6/01_confined_steady/mf6_01_confined.cbc`
- `models/mf6/01_confined_steady/heads_map.png`
- `models/mf6/01_confined_steady/run_summary.txt`

5. Запустить модуль B2 (неоднородная гидропроводность `K`):

```bash
python scripts/build_mf6_02_heterogeneous_k.py
```

6. Открыть проект B2 в ModelMuse и пройти чеклист:

```text
docs/notes/modelmuse_b2_checklist.md
```

Ожидаемые артефакты B2:

- `models/mf6/02_heterogeneous_k/mfsim.nam`
- `models/mf6/02_heterogeneous_k/mf6_02_heterogeneous_k.hds`
- `models/mf6/02_heterogeneous_k/mf6_02_heterogeneous_k.cbc`
- `models/mf6/02_heterogeneous_k/heads_map.png`
- `models/mf6/02_heterogeneous_k/k_field_map.png`
- `models/mf6/02_heterogeneous_k/run_summary.txt`

---

7. Запустить модуль B3 (recharge `RCHA`):

```bash
python scripts/build_mf6_03_recharge.py
```

8. Открыть проект B3 в ModelMuse и пройти чеклист:

```text
docs/notes/modelmuse_b3_checklist.md
```

Ожидаемые артефакты B3:

- `models/mf6/03_recharge/mfsim.nam`
- `models/mf6/03_recharge/mf6_03_recharge.hds`
- `models/mf6/03_recharge/mf6_03_recharge.cbc`
- `models/mf6/03_recharge/heads_map.png`
- `models/mf6/03_recharge/recharge_map.png`
- `models/mf6/03_recharge/run_summary.txt`

---

9. Запустить модуль B4 (pumping well `WEL` и drawdown):

```bash
python scripts/build_mf6_04_pumping_well.py
```

10. Открыть проект B4 в ModelMuse и пройти чеклист:

```text
docs/notes/modelmuse_b4_checklist.md
```

Ожидаемые артефакты B4:

- `models/mf6/04_pumping_well/mfsim.nam`
- `models/mf6/04_pumping_well/mf6_04_pumping_well.hds`
- `models/mf6/04_pumping_well/mf6_04_pumping_well.cbc`
- `models/mf6/04_pumping_well/heads_map.png`
- `models/mf6/04_pumping_well/drawdown_map.png`
- `models/mf6/04_pumping_well/run_summary.txt`

---

11. Запустить модуль B5 (сравнение граничных пакетов `RIV` / `DRN` / `GHB`):

```bash
python scripts/build_mf6_05_riv_drn_ghb.py
```

12. Открыть проект B5 в ModelMuse и пройти чеклист:

```text
docs/notes/modelmuse_b5_checklist.md
```

Ожидаемые артефакты B5:

- `models/mf6/05_riv_drn_ghb/riv/mfsim.nam`
- `models/mf6/05_riv_drn_ghb/drn/mfsim.nam`
- `models/mf6/05_riv_drn_ghb/ghb/mfsim.nam`
- `models/mf6/05_riv_drn_ghb/comparison_metrics.csv`
- `models/mf6/05_riv_drn_ghb/comparison_plot.png`
- `models/mf6/05_riv_drn_ghb/run_summary.txt`

---

## Этап B3. Recharge (`RCHA`)

Цель: показать, как равномерное площадное питание влияет на распределение напоров.

Постановка (минимально относительно B1):

- тот же grid: 1 слой, 10 x 10 ячеек;
- те же CHD слева/справа (`10` и `0`);
- однородная гидропроводность `K = 10`;
- равномерный recharge `RCHA = 1e-4` по всей площади;
- steady-state.

Definition of Done:

- модель запускается через `sim.run_simulation()`;
- сформированы карты `heads_map.png` и `recharge_map.png`;
- в `run_summary.txt` отражён процент невязки водного баланса;
- рассчитана метрика подъёма центральной области относительно боковых CHD-границ.

---

## Этап B4. Pumping well (`WEL`) и drawdown

Цель: показать, как локальная откачка формирует депрессионную воронку и понижение уровня относительно базового сценария без откачки.

Постановка (минимально относительно B1):

- тот же grid: 1 слой, 10 x 10 ячеек;
- те же CHD слева/справа (`10` и `0`);
- однородная гидропроводность `K = 10`;
- одна скважина `WEL` в центре (по умолчанию `row=5, col=5`) с расходом `Q = -500`;
- steady-state.

Definition of Done:

- модель запускается через `sim.run_simulation()`;
- сформированы карты `heads_map.png` и `drawdown_map.png`;
- в `run_summary.txt` отражён процент невязки водного баланса;
- рассчитана метрика максимального drawdown (`baseline - pumped`) и положение ячейки максимума.

---

## Этап B5. Сравнение `RIV` / `DRN` / `GHB`

Цель: показать различия поведения типовых head-dependent границ MF6 при одинаковой геометрии и близких параметрах проводимости.

Постановка (минимально относительно B1):

- тот же grid: 1 слой, 10 x 10 ячеек;
- те же CHD слева/справа (`10` и `0`);
- однородная гидропроводность `K = 10`;
- вдоль верхнего ряда (без угловых CHD-узлов) поочерёдно задаются:
  - `RIV` (stage=7, cond=20, rbot=5),
  - `DRN` (elev=7, cond=20),
  - `GHB` (bhead=7, cond=20);
- steady-state, три отдельных прогона.

Definition of Done:

- все три модели запускаются через `sim.run_simulation()`;
- сформированы `comparison_metrics.csv` и `comparison_plot.png`;
- в `run_summary.txt` сведены ключевые метрики по каждому пакету:
  - напор в центральной ячейке,
  - напор в верхней центральной ячейке,
  - суммарный обмен через пакет,
  - процент невязки водного баланса.

---

## Этап B2. Неоднородная гидропроводность `K`

Цель: показать, как неоднородность `K` меняет поле напоров при тех же граничных условиях.

Постановка (относительно B1):

- тот же grid: 1 слой, 10 x 10 ячеек;
- те же CHD слева/справа (`10` и `0`);
- базовое поле `K = 10`;
- центральная low-K линза (строки `3..6`, столбцы `3..6`) с `K = 1`;
- steady-state.

Definition of Done:

- модель запускается через `sim.run_simulation()`;
- сформированы карты `heads_map.png` и `k_field_map.png`;
- в `run_summary.txt` отражён процент невязки водного баланса;
- вычислена метрика отклонения профильной линейности по строкам.

---
## Этап B1. Первая стационарная confined-модель (MF6)

Цель: построить простую 1-слойную стационарную модель с линейным градиентом напора.

Постановка:

- 1 слой
- 10 x 10 ячеек
- `K = 10`
- слева `CHD = 10`
- справа `CHD = 0`
- no-flow на прочих границах
- steady-state

MF6 пакеты:

- `TDIS`
- `IMS`
- `GWF`
- `DIS`
- `IC`
- `NPF`
- `CHD`
- `OC`

Definition of Done:

- модель успешно запускается через `sim.run_simulation()`;
- градиент напора близок к линейному;
- сформированы график и краткий текстовый summary;
- в `run_summary.txt` отражён процент невязки водного баланса;
- дополнительно рассчитана метрика линейности профиля напора (max deviation и RMSE).

---

## Траектория обучения (обновлённая, MF6-only)

- **B1**: первая стационарная confined-модель.
- **B2**: неоднородная гидропроводность `K`.
- **B3**: recharge (`RCHA`).
- **B4**: pumping well (`WEL`) и drawdown.
- **B5**: сравнение `RIV` / `DRN` / `GHB`.
- **B6**: многослойная модель и межслойные перетоки.
- **B7**: transient-постановка через `STO`.
- **B8**: observations/time series и CSV-диагностика.

## Правила проекта

- Источник истины — Python-скрипты и выходные файлы модели.
- Для каждого шага делать минимальные изменения относительно предыдущего.
- Не смешивать разные движки в одном учебном сценарии.

## Полезные ссылки

- FloPy docs: https://flopy.readthedocs.io/en/latest/
- FloPy MF6 API: https://flopy.readthedocs.io/en/latest/source/flopy.mf6.html
- MF6 USGS: https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model
- MF6 releases: https://github.com/MODFLOW-ORG/modflow6/releases
- Официальные MF6 примеры: https://modflow6-examples.readthedocs.io/en/master/
