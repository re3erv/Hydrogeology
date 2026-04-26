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
