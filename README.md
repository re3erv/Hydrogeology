# Hydrogeology

Этот `README.md` объединяет краткое описание репозитория и полный учебный план из `plan.md`.

---

# plan.md — обучение FloPy / MODFLOW-2005 / MODFLOW 6 с визуальным контролем через PM8

Дата составления: 2026-04-26

Главная идея курса: **сначала выучить физику и классический формат MODFLOW через FloPy + MODFLOW-2005 + Processing Modflow 8, затем перейти на современную ветку FloPy + MODFLOW 6**.

Правило проекта: **источник истины — Python-код и файлы модели, а GUI используется только для проверки и визуального контроля**. Не править одну и ту же модель одновременно в PM8 и в коде, иначе быстро появится рассинхронизация.

---

## 0. Индекс источников для ИИ / Codex

Перед выполнением задач сначала использовать эти ссылки. В интернет уходить только если этих источников недостаточно или нужна проверка новой версии.

### 0.1. FloPy — официальная документация и репозиторий

- FloPy documentation, latest: https://flopy.readthedocs.io/en/latest/
- FloPy tutorials: https://flopy.readthedocs.io/en/latest/tutorials.html
- FloPy examples gallery: https://flopy.readthedocs.io/en/latest/examples.html
- FloPy GitHub repository: https://github.com/modflowpy/flopy
- Установка MODFLOW-программ через FloPy `get-modflow`: https://flopy.readthedocs.io/en/latest/md/get_modflow.html
- API: MODFLOW 6 package in FloPy: https://flopy.readthedocs.io/en/latest/source/flopy.mf6.html

### 0.2. FloPy — стартовые учебные примеры

- MODFLOW-2005 Tutorial 1 — confined steady-state flow: https://flopy.readthedocs.io/en/latest/Notebooks/mf_tutorial01.html
- MODFLOW-2005 Tutorial 2 — unconfined transient flow: https://flopy.readthedocs.io/en/latest/Notebooks/mf_tutorial02.html
- MODFLOW 6 simple model example: https://flopy.readthedocs.io/en/latest/Notebooks/mf6_simple_model_example.html
- FloPy map visualization: https://flopy.readthedocs.io/en/latest/Notebooks/plot_map_view_example.html
- MODFLOW boundaries example: https://flopy.readthedocs.io/en/latest/Notebooks/mf_boundaries_example.html
- Simple water-table solution with recharge: https://flopy.readthedocs.io/en/latest/Notebooks/mf_watertable_recharge_example.html
- MODPATH 6 with FloPy: https://flopy.readthedocs.io/en/latest/Notebooks/modpath6_example.html
- SEAWAT Henry saltwater intrusion example: https://flopy.readthedocs.io/en/latest/Notebooks/seawat_henry_example.html

### 0.3. MODFLOW 6 — USGS и официальные примеры

- USGS MODFLOW 6 page: https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model
- MODFLOW 6 downloads: https://water.usgs.gov/water-resources/software/MODFLOW-6/
- MODFLOW 6 GitHub repository: https://github.com/MODFLOW-ORG/modflow6
- MODFLOW 6 releases: https://github.com/MODFLOW-ORG/modflow6/releases
- MODFLOW 6 examples documentation: https://modflow6-examples.readthedocs.io/en/master/
- MODFLOW 6 examples GitHub repository: https://github.com/MODFLOW-ORG/modflow6-examples
- How official MODFLOW 6 examples are structured: https://github.com/MODFLOW-ORG/modflow6-examples/blob/develop/DEVELOPER.md
- MODFLOW and Related Programs GitHub organization: https://github.com/MODFLOW-ORG

### 0.4. MODFLOW-2005 / MODFLOW-NWT — USGS

- MODFLOW-2005 USGS page: https://www.usgs.gov/software/modflow-2005-usgs-three-dimensional-finite-difference-ground-water-model
- Online Guide to MODFLOW-2005: https://water.usgs.gov/ogw/modflow/MODFLOW-2005-Guide/
- MODFLOW-2005 Name File description: https://water.usgs.gov/ogw/modflow/MODFLOW-2005-Guide/name_file.html
- MODFLOW-NWT Online Guide: https://water.usgs.gov/ogw/modflow-nwt/MODFLOW-NWT-Guide/
- Combined MODFLOW guide: https://water.usgs.gov/nrp/gwsoftware/modflow2000/MFDOC/index.html

### 0.5. Processing Modflow 8 / PMWIN

- Simcore archive with Processing Modflow 8 download and public-domain key: https://www.simcore.com/wp/archive/
- PM8 release notes: https://www.simcore.com/wp/pm8-release-notes/
- PM8 user guide PDF: https://www.simcore.com/files/pm/v8/pm8.pdf
- Legacy PMWIN software page: https://www.pmwin.net/software.htm

Important note: использовать PM8 как визуальный инспектор преимущественно для **MODFLOW-2005 / MODFLOW-NWT**. Для **MODFLOW 6** не планировать PM8 как основной GUI.

### 0.6. Визуализация MODFLOW 6 и альтернативные GUI

- ModelMuse import MODFLOW 6 model: https://water.usgs.gov/nrp/gwsoftware/ModelMuse/Help/import-modflow-6-model-dialog-.html
- Model Viewer for MODFLOW 6: https://www.usgs.gov/software/model-viewer-a-program-three-dimensional-visualization-groundwater-model-results
- ModelMuse MODFLOW 6 example: https://water.usgs.gov/nrp/gwsoftware/ModelMuse/Help/modflow_6_example.html

### 0.7. Калибровка, PEST, pyEMU — на поздний этап

- FloPy PEST tutorial: https://flopy.readthedocs.io/en/latest/tutorials.html#pest
- pyEMU documentation: https://pyemu.readthedocs.io/
- pyEMU GitHub repository: https://github.com/pypest/pyemu

### 0.8. Готовые открытые примеры

- Pleasant Lake worked FloPy example, USGS: https://github.com/DOI-USGS/pleasant-lake-flopy-example
- MODFLOW 6 official examples: https://github.com/MODFLOW-ORG/modflow6-examples
- FloPy example gallery: https://flopy.readthedocs.io/en/latest/examples.html
- Symple FloPy course examples: https://github.com/rhugman/symple_flopy

---

## 1. Общая архитектура учебного репозитория

Рекомендуемая структура проекта:

```text
modflow-learning/
  plan.md
  README.md
  environment.yml
  pyproject.toml              # опционально, если решим делать пакет
  .gitignore
  data/
    raw/
    processed/
  models/
    mf2005/
      01_confined_steady/
      02_heterogeneous_k/
      03_recharge/
      04_well/
      05_river_drain_ghb/
      06_multilayer/
      07_transient/
      08_unconfined_nwt/
    mf6/
      01_confined_steady/
      02_rebuild_mf2005_case/
      03_transient_sto/
      04_gwt_transport/
      05_disv_optional/
      06_scenarios/
  notebooks/
    00_environment_check.ipynb
    01_mf2005_first_model.ipynb
    02_mf6_first_model.ipynb
  src/
    modflow_learning/
      __init__.py
      paths.py
      plotting.py
      budget.py
      validation.py
  scripts/
    build_mf2005_01_confined.py
    build_mf6_01_confined.py
  tests/
    test_environment.py
    test_models_run.py
  docs/
    screenshots_pm8/
    notes/
```

Рабочее правило для Windows + PM8: пути к моделям делать короткими, без пробелов, без кириллицы и без спецсимволов, например `C:\gw\modflow-learning\models\mf2005\01_confined_steady`.

---

## 2. Границы совместимости PM8, FloPy и MODFLOW 6

### 2.1. Что отслеживаем через PM8

Через Processing Modflow 8 отслеживаем модели, которые FloPy пишет в формате классического MODFLOW:

- MODFLOW-2005;
- MODFLOW-NWT;
- в отдельных случаях MODFLOW-2000, если понадобится сравнение со старыми материалами.

Контрольный процесс:

```text
Python / FloPy script
  -> write_input()
  -> MODFLOW-2005 Name File + package files
  -> run_model()
  -> PM8 import / convert native MODFLOW model
  -> visual check: grid, K, IBOUND, recharge, wells, rivers, heads, budget
```

### 2.2. Что не отслеживаем через PM8

Для MODFLOW 6 PM8 не использовать как основной просмотрщик. Для MF6 использовать:

- FloPy plots;
- matplotlib / pandas summaries;
- ModelMuse import MF6, если задача подходит под ограничения импорта;
- Model Viewer for MODFLOW 6;
- прямую проверку файлов `mfsim.nam`, `*.nam`, `*.dis`, `*.npf`, `*.chd`, `*.wel`, `*.rch`, `*.oc`, `*.lst`, `*.hds`, `*.cbc`.

---

## 3. Как работать с Codex по этому плану

Шаблон запроса к Codex:

```text
Открой plan.md и выполни пункт <ID пункта>.
Не переходи к следующим пунктам.
Сохрани код в указанной структуре проекта.
После выполнения:
1. покажи, какие файлы созданы или изменены;
2. покажи команду запуска;
3. покажи ожидаемые выходные файлы MODFLOW;
4. проверь, что модель запускается;
5. если пункт относится к MODFLOW-2005, укажи, какой .nam файл открыть/import в Processing Modflow 8.
```

Шаблон ограничения для Codex:

```text
Не переписывай архитектуру проекта без необходимости.
Не добавляй новые зависимости, если задачу можно решить через numpy, pandas, matplotlib и flopy.
Не смешивай MODFLOW-2005 и MODFLOW 6 в одном скрипте, кроме специальных сравнительных задач.
Для каждого учебного шага делай минимальное изменение относительно предыдущего шага.
```

---

## 4. Фаза A — подготовка окружения

### A0. Создать базовый репозиторий

Цель: создать минимальный проект с понятной структурой.

Задачи:

- [ ] Создать структуру папок из раздела 1.
- [ ] Создать `.gitignore` для Python, Jupyter, MODFLOW binary outputs и временных файлов.
- [ ] Создать `README.md` с коротким описанием курса.
- [ ] Создать `environment.yml` или инструкции для `venv`.

Definition of Done:

- [ ] `python -c "import flopy; print(flopy.__version__)"` работает.
- [ ] В проекте есть `plan.md`, `README.md`, `.gitignore`, `environment.yml`.

### A1. Установить MODFLOW executables через FloPy

Цель: научиться получать `mf6`, `mf2005`, `mfnwt` и другие исполняемые файлы воспроизводимым способом.

Задачи:

- [ ] Создать `notebooks/00_environment_check.ipynb` или `scripts/check_environment.py`.
- [ ] Проверить импорт `flopy`, `numpy`, `pandas`, `matplotlib`.
- [ ] Использовать `flopy.utils.get_modflow()` или команду `get-modflow`.
- [ ] Проверить доступность `mf6`, `mf2005`, `mfnwt`.

Definition of Done:

- [ ] Скрипт выводит версии Python, FloPy, NumPy.
- [ ] Скрипт находит executable-файлы или сообщает понятную инструкцию, куда их положить.

### A2. Установить и проверить PM8

Цель: подготовить GUI-контроль для ветки MODFLOW-2005.

Задачи:

- [ ] Скачать PM8 из Simcore archive.
- [ ] Активировать public-domain key, указанный на странице Simcore archive.
- [ ] Проверить запуск PM8.
- [ ] Создать папку `docs/screenshots_pm8/` для скриншотов проверки моделей.

Definition of Done:

- [ ] PM8 запускается.
- [ ] Пользователь понимает, где в PM8 импортировать или конвертировать native MODFLOW model.
- [ ] Зафиксирована версия PM8, ОС и путь установки в `docs/notes/pm8_setup.md`.

---

## 5. Фаза B — MODFLOW-2005 + FloPy + PM8 как визуальный инспектор

### B1. Первая стационарная confined-модель

Цель: построить простую модель с линейным градиентом напора.

Модель:

- 1 слой;
- 10 x 10 ячеек;
- confined aquifer;
- `K = 10`;
- слева constant head = 10;
- справа constant head = 0;
- no-flow сверху/снизу/по остальным границам;
- steady-state.

FloPy / MODFLOW-2005 пакеты:

- `DIS`;
- `BAS`;
- `LPF`;
- `PCG`;
- `OC`.

Задачи:

- [ ] Создать `scripts/build_mf2005_01_confined.py`.
- [ ] Записать input-файлы через `mf.write_input()`.
- [ ] Запустить модель через `mf.run_model()`.
- [ ] Прочитать `.hds` и `.cbc`.
- [ ] Построить карту heads.
- [ ] Импортировать `.nam` в PM8 и проверить сетку, IBOUND, heads.

Definition of Done:

- [ ] В модели есть ожидаемый почти линейный градиент.
- [ ] Water budget residual мал.
- [ ] В README к задаче указан `.nam` файл для PM8.
- [ ] В `docs/screenshots_pm8/` сохранен скриншот проверки.

### B2. Неоднородная гидропроводность K

Цель: понять влияние пространственной неоднородности K.

Изменение относительно B1:

- добавить 2–3 зоны K: например песок, суглинок, глина;
- хранить массив K в явном виде;
- визуализировать `hk` и heads.

Задачи:

- [ ] Скопировать B1 в `models/mf2005/02_heterogeneous_k/`.
- [ ] Добавить функцию генерации массива `hk`.
- [ ] Построить карту K.
- [ ] Сравнить heads с B1.
- [ ] Проверить импорт в PM8.

Definition of Done:

- [ ] Видно, как изопьезы искривляются в зонах разного K.
- [ ] PM8 корректно показывает массив `hk`.

### B3. Recharge

Цель: добавить инфильтрационное питание и увидеть его в балансе.

Изменение относительно B2:

- добавить `RCH`;
- начать с равномерного recharge;
- затем сделать зонированный recharge.

Задачи:

- [ ] Добавить пакет `RCH`.
- [ ] Построить карту recharge.
- [ ] Проверить budget: recharge должен появиться как входной поток.
- [ ] Проверить модель в PM8.

Definition of Done:

- [ ] Водный баланс показывает вклад recharge.
- [ ] Карта heads изменилась физически правдоподобно.

### B4. Pumping well

Цель: добавить водозаборную скважину и воронку депрессии.

Изменение относительно B3:

- добавить `WEL`;
- одна скважина в центре;
- несколько сценариев дебита.

Задачи:

- [ ] Добавить пакет `WEL`.
- [ ] Сформировать 3 сценария pumping rate.
- [ ] Построить карту drawdown относительно модели без скважины.
- [ ] Проверить скважину в PM8.

Definition of Done:

- [ ] Видна депрессионная воронка.
- [ ] Увеличение pumping rate увеличивает drawdown.
- [ ] PM8 показывает положение скважины и дебит.

### B5. River / Drain / General Head Boundary

Цель: разобраться в типовых граничных условиях MODFLOW.

Изменение относительно B4:

- добавить по отдельности `RIV`, `DRN`, `GHB`;
- не смешивать все сразу в одной первой версии;
- сделать отдельные подпапки или сценарии.

Задачи:

- [ ] Создать сценарий `riv`.
- [ ] Создать сценарий `drn`.
- [ ] Создать сценарий `ghb`.
- [ ] Для каждого сценария построить heads и budget.
- [ ] Проверить импорт в PM8.

Definition of Done:

- [ ] Понятно, чем физически отличаются RIV, DRN и GHB.
- [ ] В budget видны соответствующие статьи.

### B6. Многослойная модель

Цель: добавить вертикальное строение водоносной системы.

Модель:

- 3 слоя;
- разные `hk`, `vka` или `vk`;
- скважина может быть в одном или нескольких слоях;
- сравнить межслойные перетоки.

Задачи:

- [ ] Перенести сетку в 3D.
- [ ] Настроить `botm` и свойства слоев.
- [ ] Построить heads по слоям.
- [ ] Построить cross-section.
- [ ] Проверить в PM8 слой за слоем.

Definition of Done:

- [ ] Скрипт строит карты по каждому слою.
- [ ] В PM8 можно визуально проверить свойства каждого слоя.

### B7. Transient model

Цель: добавить время, storage и графики drawdown.

Изменение относительно B6:

- несколько stress periods;
- storage properties;
- pumping schedule.

Задачи:

- [ ] Настроить `nper`, `perlen`, `nstp`, `steady`.
- [ ] Добавить `STO`-аналог для классической ветки через соответствующие параметры LPF/BCF/NWT-подхода.
- [ ] Задать временной ряд дебита скважины.
- [ ] Построить hydrograph в наблюдательной ячейке.
- [ ] Проверить в PM8 transient results.

Definition of Done:

- [ ] Есть график напора во времени.
- [ ] Понятно, как меняется budget по stress periods.

### B8. MODFLOW-NWT / unconfined

Цель: познакомиться с безнапорной постановкой и проблемами сходимости.

Задачи:

- [ ] Перевести модель в unconfined режим.
- [ ] Использовать NWT, если обычный solver плохо сходится.
- [ ] Проверить влияние начальных условий.
- [ ] Проверить dry / rewetting поведение.
- [ ] Проверить, что PM8 корректно читает модель NWT.

Definition of Done:

- [ ] Модель сходится.
- [ ] В notes описано, почему NWT нужен для части unconfined-задач.

---

## 6. Фаза C — переход к MODFLOW 6 через FloPy

### C1. Первая эквивалентная MF6-модель

Цель: собрать аналог B1 в MODFLOW 6.

MF6 компоненты:

- simulation;
- `TDIS`;
- `IMS`;
- `GWF`;
- `DIS`;
- `IC`;
- `NPF`;
- `CHD`;
- `OC`.

Задачи:

- [ ] Создать `scripts/build_mf6_01_confined.py`.
- [ ] Сделать ту же геометрию, что в B1.
- [ ] Записать input через `sim.write_simulation()`.
- [ ] Запустить через `sim.run_simulation()`.
- [ ] Прочитать `.hds` и `.cbc`.
- [ ] Построить карту heads.

Definition of Done:

- [ ] Результат близок к B1.
- [ ] В notes описано соответствие пакетов MODFLOW-2005 и MODFLOW 6.

### C2. Таблица соответствия MODFLOW-2005 и MODFLOW 6

Цель: закрепить переход между старыми и новыми пакетами.

Задачи:

- [ ] Создать `docs/notes/mf2005_to_mf6_mapping.md`.
- [ ] Сравнить минимум эти пары:
  - `DIS` → `DIS`;
  - `BAS` → `IC` + часть логики active/idomain;
  - `LPF/UPW` → `NPF`;
  - `PCG/NWT` → `IMS`;
  - `WEL` → `WEL`;
  - `RCH` → `RCHA` или `RCH`, в зависимости от постановки;
  - `RIV`, `DRN`, `GHB`, `CHD` → соответствующие GWF packages;
  - `OC` → `OC`.

Definition of Done:

- [ ] В таблице есть пакет, назначение, ключевые параметры, пример использования во FloPy.

### C3. Перенести задачи B2–B5 в MF6

Цель: повторить неоднородный K, recharge, well, river/drain/ghb в MF6.

Задачи:

- [ ] Создать сценарий heterogeneous K.
- [ ] Создать сценарий recharge.
- [ ] Создать сценарий pumping well.
- [ ] Создать сценарий river/drain/ghb.
- [ ] Для каждого сценария построить heads, drawdown, budget summary.

Definition of Done:

- [ ] Результаты физически сопоставимы с MODFLOW-2005 веткой.
- [ ] В notes указаны отличия синтаксиса FloPy MF6.

### C4. Transient MF6 через STO

Цель: освоить storage в MODFLOW 6.

Задачи:

- [ ] Добавить `STO` package.
- [ ] Настроить steady/transient stress periods.
- [ ] Сделать pumping schedule через stress period data или time series.
- [ ] Построить hydrographs.
- [ ] Сравнить с B7.

Definition of Done:

- [ ] Есть корректный график изменения напора во времени.
- [ ] В budget видны storage terms.

### C5. Наблюдения и time series в MF6

Цель: научиться строить модели, удобные для анализа и калибровки.

Задачи:

- [ ] Добавить observation package для heads.
- [ ] Добавить time series для pumping или river stage.
- [ ] Сохранить output в CSV.
- [ ] Прочитать CSV через pandas.
- [ ] Построить hydrograph по наблюдениям.

Definition of Done:

- [ ] Наблюдения сохраняются отдельно и читаются без ручного парсинга binary files.

---

## 7. Фаза D — визуализация, проверка и диагностика

### D1. Общие функции визуализации

Цель: вынести повторяющийся код в `src/modflow_learning/plotting.py`.

Функции:

- [ ] `plot_array()` — карта массива;
- [ ] `plot_heads()` — карта heads;
- [ ] `plot_drawdown()` — разность heads;
- [ ] `plot_boundary_cells()` — положение граничных условий;
- [ ] `plot_cross_section()` — разрез.

Definition of Done:

- [ ] Скрипты B и C используют общие функции.
- [ ] Нет копипаста plotting-кода в каждом сценарии.

### D2. Общая проверка water budget

Цель: автоматизировать контроль баланса.

Функции:

- [ ] прочитать listing file или budget output;
- [ ] вывести входы, выходы, percent discrepancy;
- [ ] сохранять `budget_summary.csv`.

Definition of Done:

- [ ] У каждой модели есть summary-файл с балансом.
- [ ] В README написано, какой threshold считать приемлемым для учебных моделей.

### D3. ModelMuse / Model Viewer для MF6

Цель: протестировать визуальный контроль MF6 вне PM8.

Задачи:

- [ ] Импортировать простую MF6-модель в ModelMuse.
- [ ] Проверить ограничения импорта.
- [ ] Открыть результаты в Model Viewer for MODFLOW 6.
- [ ] Сохранить краткие notes и скриншоты.

Definition of Done:

- [ ] Есть инструкция `docs/notes/mf6_visual_check.md`.

---

## 8. Фаза E — более сложные гидрогеологические задачи

### E1. Частицы / capture zone

Цель: познакомиться с траекторным анализом.

Варианты:

- классическая ветка: MODFLOW-2005 + MODPATH 6/7;
- современная ветка: MF6 + MODPATH 7 или MF6 PRT, если выбран соответствующий стек.

Задачи:

- [ ] Построить capture zone для pumping well.
- [ ] Визуализировать pathlines.
- [ ] Сравнить влияние K и pumping rate.

Definition of Done:

- [ ] Есть карта pathlines или endpoints.

### E2. Transport

Цель: перейти от flow к contaminant transport.

Варианты:

- MF6 GWT как современная ветка;
- MT3DMS/SEAWAT как историческая ветка, если нужна совместимость с PM8/старой литературой.

Задачи:

- [ ] Создать простой перенос от источника загрязнения.
- [ ] Добавить advection/dispersion.
- [ ] Построить карты концентраций во времени.
- [ ] Проверить mass balance.

Definition of Done:

- [ ] Есть несколько временных срезов концентрации.

### E3. DISV / нерегулярные сетки

Цель: понять, зачем нужны современные сетки.

Задачи:

- [ ] Создать простой DISV пример.
- [ ] Сравнить с DIS.
- [ ] Проверить, где ломается импорт в GUI.
- [ ] Зафиксировать ограничения.

Definition of Done:

- [ ] Есть notes: когда использовать DIS, DISV, DISU.

### E4. Сценарное моделирование

Цель: использовать силу Python — массовые прогоны.

Сценарии:

- pumping rate;
- recharge multiplier;
- river stage;
- hydraulic conductivity zones;
- drought / wet year.

Задачи:

- [ ] Создать функцию `run_scenario(params)`.
- [ ] Сохранять результаты в отдельные папки.
- [ ] Собирать итоговую таблицу `scenario_summary.csv`.
- [ ] Строить график зависимости drawdown от параметра.

Definition of Done:

- [ ] Один скрипт прогоняет серию сценариев и собирает таблицу результатов.

---

## 9. Фаза F — калибровка и неопределенность

Эта фаза только после уверенного владения B–E.

### F1. Ручная калибровка

Цель: понять смысл калибровки без PEST.

Задачи:

- [ ] Создать synthetic observations.
- [ ] Добавить шум.
- [ ] Подбирать K и recharge вручную.
- [ ] Считать RMSE/MAE/bias.

Definition of Done:

- [ ] Есть таблица observed vs simulated.
- [ ] Есть график residuals.

### F2. pyEMU / PEST++ baseline

Цель: познакомиться с автоматической калибровкой.

Задачи:

- [ ] Изучить FloPy PEST tutorial.
- [ ] Изучить pyEMU examples.
- [ ] Создать простую parameter estimation задачу для K или recharge.
- [ ] Не начинать с полноценной полевой модели.

Definition of Done:

- [ ] Есть минимальный рабочий PEST/pyEMU пример.
- [ ] В notes описано, какие файлы являются template/input/output/control.

---

## 10. Методика нарастания сложности

Не добавлять одновременно новую физику и новую программную сложность.

Правильный порядок:

1. Сначала простая steady confined модель.
2. Потом неоднородный K.
3. Потом recharge.
4. Потом pumping well.
5. Потом RIV/DRN/GHB.
6. Потом несколько слоев.
7. Потом transient.
8. Потом unconfined/NWT.
9. Потом перенос в MODFLOW 6.
10. Потом observations/time series.
11. Потом particle tracking.
12. Потом transport.
13. Потом сценарии.
14. Потом калибровка.

Антипаттерн: одновременно переходить на MF6, добавлять transient, GWT, DISV и калибровку. Так будет трудно понять, где ошибка — в физике, сетке, формате input или Python-коде.

---

## 11. Минимальные стандарты качества для каждой задачи

Каждый учебный пункт должен иметь:

- [ ] отдельную папку модели;
- [ ] один главный скрипт сборки модели;
- [ ] явный workspace;
- [ ] запуск модели из кода;
- [ ] чтение результатов из кода;
- [ ] хотя бы один график;
- [ ] water budget summary;
- [ ] короткий `README.md` внутри папки модели;
- [ ] указание, можно ли смотреть модель через PM8;
- [ ] если можно, указание точного `.nam` файла для PM8;
- [ ] если нельзя, указание альтернативного способа визуального контроля.

---

## 12. Чек-лист для каждого pull request / изменения

Перед фиксацией изменения проверить:

- [ ] Код запускается из чистого окружения.
- [ ] Пути относительные, не завязаны на конкретный компьютер.
- [ ] Нет больших binary outputs в git, если они не нужны.
- [ ] Есть reproducible seed, если используются случайные данные.
- [ ] Модель сходится.
- [ ] Budget discrepancy приемлем.
- [ ] Графики сохраняются в `figures/`.
- [ ] Для MODFLOW-2005 ветки проверен импорт в PM8 или явно написано, почему не проверялся.
- [ ] Для MODFLOW 6 ветки не заявляется совместимость с PM8 без отдельной проверки.

---

## 13. Быстрые команды, которые стоит держать в README

```bash
# создать окружение через conda
conda env create -f environment.yml
conda activate modflow-learning

# проверить установку Python-зависимостей
python scripts/check_environment.py

# установить MODFLOW-related executables через FloPy
get-modflow :flopy

# запустить первую MODFLOW-2005 модель
python scripts/build_mf2005_01_confined.py

# запустить первую MODFLOW 6 модель
python scripts/build_mf6_01_confined.py
```

---

## 14. Что просить у Codex в первую очередь

Рекомендуемая первая серия запросов:

1. `Выполни A0: создай структуру репозитория, .gitignore, README.md и environment.yml.`
2. `Выполни A1: создай scripts/check_environment.py и проверь установку FloPy/MODFLOW executables.`
3. `Выполни B1: создай первую MODFLOW-2005 confined steady-state модель, которую можно открыть в PM8.`
4. `Добавь для B1 README с точным .nam файлом и инструкцией проверки через PM8.`
5. `Выполни C1: создай аналогичную модель в MODFLOW 6 и сравни heads с B1.`

---

## 15. Решения, принятые в плане

- PM8 используется как бесплатный визуальный инспектор для классической ветки MODFLOW-2005/NWT.
- MODFLOW 6 изучается отдельно, без требования совместимости с PM8.
- Для MF6 визуальный контроль идет через FloPy plots, ModelMuse и Model Viewer for MODFLOW 6.
- Каждый следующий учебный шаг меняет только один существенный элемент модели.
- Все задачи должны быть воспроизводимы из кода.
