# ModelMuse checklist — этап B8 (observations/time series и CSV-диагностика)

Цель: убедиться, что в MF6-модели настроены наблюдения (`UTL-OBS`), результаты пишутся в CSV, и по ним формируются простые диагностические метрики.

## 1) Открытие проекта

Откройте name-файл:

- `models/mf6/08_observations_csv/mfsim.nam`

Проверьте, что проект загружается как MODFLOW 6.

## 2) Проверка базовой постановки

Сверьте, что базовая transient-схема совпадает с B7:

- `DIS`: `nlay=1`, `nrow=10`, `ncol=10`, `top=10`, `botm=0`, `delr=delc=100`;
- `TDIS`: 3 периода (SP1=1 день steady, SP2=30 дней pumping, SP3=30 дней recovery);
- `NPF/STO`: `k=10`, `icelltype=0`, `ss=1e-5`, `sy=0.15`, `iconvert=0`;
- `CHD` слева/справа (`10` и `0`) и `WEL` в центре (`Q=-500` только на SP2).

## 3) Проверка наблюдений (OBS)

Проверьте, что заданы непрерывные наблюдения напора как минимум в трёх точках:

- `h_center` — центральная ячейка (скважина);
- `h_upgradient` — апгрейдиентная точка;
- `h_downgradient` — даунградиентная точка.

Ожидание: после расчёта формируется CSV-файл наблюдений.

## 4) Проверка файлов результатов B8

В папке B8 должны появиться:

- `head_observations.csv`
- `observations_diagnostics.csv`
- `observations_timeseries.png`
- `run_summary.txt`

## 5) Проверка CSV-диагностики

Откройте `observations_diagnostics.csv` и убедитесь, что присутствуют метрики:

- `drawdown_end_pumping`;
- `residual_drawdown_end_recovery`;
- `min_center_head`;
- доли монотонности:
  - `pumping_nonincreasing_share`;
  - `recovery_nondecreasing_share`.

Sanity check:

- к концу SP2 понижение (`drawdown`) положительно и заметно;
- к концу SP3 остаточное понижение меньше, чем к концу SP2;
- доли монотонности близки к 1.0 для корректного отклика без сильного численного шума.

## 6) Проверка краткого отчёта

В `run_summary.txt` должны быть ссылки на:

- CSV наблюдений;
- CSV диагностики;
- график временных рядов;
- процент невязки водного баланса (`Budget percent discrepancy`).

### Пояснение

я открыл модель в model muse ссылка на github: https://github.com/re3erv/Hydrogeology.git. Модель создана скриптом python scripts/build_mf6_08_observations_csv.py. Помоги наглядно увидеть (посмотреть) исходные данные модели и результаты моделирования.
Разберу структуру репозитория и сам скрипт сборки, затем дам понятный маршрут: что смотреть прямо в ModelMuse, какие входные файлы/CSV открыть, и как быстро построить карты/графики результатов через Python.
Received app response
Уже видно ключевое: это маленькая 1-слойная MF6-модель 10×10, с постоянными напорами слева/справа, скважиной в центре и CSV-наблюдениями по трем точкам. Сейчас найду, какие вспомогательные файлы и инструкции уже есть в репозитории, чтобы не предлагать лишнее.
Received app response
Received app response
Thought for 55s
Да. Для этой модели удобнее смотреть в двух местах одновременно: геометрию/пакеты в ModelMuse, а временные ряды и диагностику — через CSV/PNG, которые уже делает скрипт.
1. Что это за модель B8
Скрипт scripts/build_mf6_08_observations_csv.py строит transient MF6-модель:
•	сетка: 1 слой, 10×10 ячеек, delr=delc=100, top=10, botm=0; 
•	слева CHD=10, справа CHD=0; 
•	K=10, ss=1e-5, sy=0.15; 
•	3 stress period: 1 день steady, затем 30 дней pumping, затем 30 дней recovery; 
•	скважина в центре: Q=-500 только во втором периоде; 
•	наблюдения напора: h_center, h_upgradient, h_downgradient; 
•	результаты наблюдений пишутся в head_observations.csv. 
2. Сначала пересобери и запусти модель
Из корня репозитория:
conda env create -f environment.yml
conda activate modflow-learning

python scripts/check_environment.py --diagnose-only
python scripts/build_mf6_08_observations_csv.py
Окружение в репозитории уже рассчитано на python=3.11, numpy, pandas, matplotlib, jupyterlab и flopy. 
После запуска смотри папку:
models/mf6/08_observations_csv/
Главные файлы:
mfsim.nam
mf6_08_observations_csv.hds
mf6_08_observations_csv.cbc
head_observations.csv
observations_diagnostics.csv
observations_timeseries.png
run_summary.txt
Именно эти B8-артефакты указаны в README и чеклисте ModelMuse. 
3. Как смотреть исходные данные в ModelMuse
В ModelMuse открывай не Python-скрипт, а MF6 simulation name file:
models/mf6/08_observations_csv/mfsim.nam
Лучший путь:
File → Import → MODFLOW 6 Model
и выбрать mfsim.nam. В справке ModelMuse этот диалог описан именно как способ импортировать существующую MODFLOW 6-модель по simulation name file. 
Что проверить в ModelMuse:
Что смотреть	Ожидаемое значение
Grid / DIS	1 слой, 10 строк, 10 столбцов
Cell size	delr=100, delc=100
Top / Bottom	top=10, botm=0
NPF	K=10, confined setup
STO	ss=1e-5, sy=0.15, transient во 2–3 периодах
CHD	левый край 10, правый край 0
WEL	центральная скважина, Q=-500 только в SP2
OBS	3 наблюдения напора
Важно: в Python/FloPy индексы well_row=5, well_col=5 — это фактически центральная область сетки 10×10. В интерфейсе, где строки/столбцы могут показываться с 1, это может выглядеть как 6-я строка, 6-й столбец.
4. Как смотреть результаты в ModelMuse
После открытия модели импортируй результаты отдельно:
File → Import → Model Results...
или кнопкой Import and display model results.
Сначала выбери:
mf6_08_observations_csv.hds
ModelMuse умеет импортировать head/drawdown/flow results и после импорта относит их к наборам данных Optional | Model Results; можно сразу выбрать раскраску или контуры по импортированному набору. 
Для этой модели особенно полезно импортировать/сравнить три момента времени:
Время	Что должно быть видно
t = 1 день	базовый градиент слева направо
t = 31 день	конец откачки, максимальное понижение у скважины
t = 61 день	восстановление после остановки откачки
Потом можно импортировать бюджет:
mf6_08_observations_csv.cbc
В справке ModelMuse прямо указано, что можно импортировать .cbc и смотреть flow terms / specific discharge components. 
5. Самый наглядный набор файлов вне ModelMuse
Открой эти файлы прямо из папки модели:
observations_timeseries.png
Это готовый график временных рядов h_center, h_upgradient, h_downgradient.
head_observations.csv
Это сырые временные ряды наблюдений.
observations_diagnostics.csv
Там должны быть метрики:
•	drawdown_end_pumping; 
•	residual_drawdown_end_recovery; 
•	min_center_head; 
•	pumping_nonincreasing_share; 
•	recovery_nondecreasing_share. 
Их наличие и sanity-check описаны в B8-чеклисте. 
6. Быстрый Python-скрипт для карт напоров и drawdown
Сохрани это как, например:
scripts/visualize_mf6_08_results.py
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WS = PROJECT_ROOT / "models" / "mf6" / "08_observations_csv"

SIM_NAME = "mf6_08_observations_csv"
HDS = WS / f"{SIM_NAME}.hds"
OBS_CSV = WS / "head_observations.csv"


def save_head_map(time_value: float, out_name: str) -> None:
    hds = flopy.utils.HeadFile(str(HDS))
    head = hds.get_data(totim=time_value)[0]

    fig, ax = plt.subplots(figsize=(6, 5), dpi=140)
    im = ax.imshow(head, origin="upper")
    ax.set_title(f"Head map, t={time_value:g} days")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")

    # скважина: FloPy row=5, col=5
    ax.scatter([5], [5], marker="x", s=80, label="WEL / h_center")
    ax.legend()

    fig.colorbar(im, ax=ax, label="Head")
    fig.tight_layout()
    fig.savefig(WS / out_name)
    plt.close(fig)


def save_drawdown_maps() -> None:
    hds = flopy.utils.HeadFile(str(HDS))

    h_t1 = hds.get_data(totim=1.0)[0]
    h_t31 = hds.get_data(totim=31.0)[0]
    h_t61 = hds.get_data(totim=61.0)[0]

    dd_31 = h_t1 - h_t31
    dd_61 = h_t1 - h_t61

    for arr, title, out_name in [
        (dd_31, "Drawdown at end of pumping, t=31 days", "b8_drawdown_t31.png"),
        (dd_61, "Residual drawdown after recovery, t=61 days", "b8_drawdown_t61.png"),
    ]:
        fig, ax = plt.subplots(figsize=(6, 5), dpi=140)
        im = ax.imshow(arr, origin="upper", vmin=0)
        ax.set_title(title)
        ax.set_xlabel("Column")
        ax.set_ylabel("Row")
        ax.scatter([5], [5], marker="x", s=80, label="WEL / h_center")
        ax.legend()
        fig.colorbar(im, ax=ax, label="Drawdown")
        fig.tight_layout()
        fig.savefig(WS / out_name)
        plt.close(fig)


def save_observation_plot() -> None:
    df = pd.read_csv(OBS_CSV)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=140)

    time_col = df.columns[0]
    for col in df.columns[1:]:
        ax.plot(df[time_col], df[col], linewidth=2, label=col)

    ax.axvline(1.0, linestyle="--", linewidth=1)
    ax.axvline(31.0, linestyle="--", linewidth=1)
    ax.set_title("B8 head observations")
    ax.set_xlabel("Time, days")
    ax.set_ylabel("Head")
    ax.grid(alpha=0.25)
    ax.legend()

    fig.tight_layout()
    fig.savefig(WS / "b8_observations_timeseries_extra.png")
    plt.close(fig)


def main() -> None:
    if not HDS.exists():
        raise FileNotFoundError(f"Run the model first. Missing: {HDS}")

    save_head_map(1.0, "b8_head_t1.png")
    save_head_map(31.0, "b8_head_t31.png")
    save_head_map(61.0, "b8_head_t61.png")
    save_drawdown_maps()
    save_observation_plot()

    print("Saved extra B8 visualizations in:")
    print(WS)


if __name__ == "__main__":
    main()
Запуск:
python scripts/visualize_mf6_08_results.py
После этого в models/mf6/08_observations_csv/ появятся:
b8_head_t1.png
b8_head_t31.png
b8_head_t61.png
b8_drawdown_t31.png
b8_drawdown_t61.png
b8_observations_timeseries_extra.png
7. Как интерпретировать картинку
Для B8 ожидаемая история такая:
t=1     — установился базовый градиент от CHD=10 к CHD=0
t=31    — закончилась откачка, в центре максимальное понижение
t=61    — откачка выключена, напоры восстанавливаются
В CSV-графике центральная точка h_center должна падать во время SP2 и расти во время SP3. Апгрейдиентная и даунградиентная точки должны реагировать слабее, потому что они дальше от скважины.
что такое Specific_Storage и Specific_Yield
Specific Storage (Ss, удельная упругая водоотдача) и Specific Yield (Sy, гравитационная водоотдача) — это параметры хранения воды в водоносном горизонте.
Specific Storage — Ss
Specific Storage показывает, сколько воды выделится из единичного объёма водоносной породы при снижении напора на 1 метр.
Обычно используется для напорных / confined условий, когда пласт полностью насыщен, а вода выходит за счёт:
•	упругого сжатия скелета породы; 
•	расширения воды при снижении давления. 
Единицы измерения:
1/m
В твоей модели B8:
ss = 1.0e-5
Это значит: при изменении напора на 1 м из каждого кубометра насыщенной породы высвобождается очень малая доля воды за счёт упругого хранения.
Specific Yield — Sy
Specific Yield показывает, какая доля воды может вытечь из породы под действием силы тяжести при понижении уровня грунтовых вод.
Обычно используется для безнапорных / unconfined условий, когда меняется положение свободной поверхности.
Единицы измерения:
безразмерная величина
В твоей модели B8:
sy = 0.15
Это значит: теоретически около 15% объёма породы может отдать воду при осушении порового пространства.
Главное отличие
Параметр	Где важен	Что описывает	Типичная величина
Ss	confined aquifer	упругое хранение воды	маленькая, например 1e-6–1e-4 1/m
Sy	unconfined aquifer	гравитационный дренаж пор	больше, например 0.05–0.30
В контексте MODFLOW 6
В пакете STO задаются оба параметра:
flopy.mf6.ModflowGwfsto(
    gwf,
    iconvert=0,
    ss=1.0e-5,
    sy=0.15,
)
Но в твоей B8-модели стоит:
iconvert = 0
Это означает confined / напорная постановка. Поэтому главным параметром хранения фактически является Specific Storage (Ss).
Specific Yield (Sy) в такой постановке задан, но почти не играет роли, потому что модель не рассчитывает осушение/насыщение ячеек как в безнапорном горизонте.
Простая аналогия:
Ss — вода выходит потому, что пласт "сжимается как пружина".
Sy — вода выходит потому, что поры реально осушаются и вода стекает вниз.
Для твоей модели B8: смотри на Ss = 1e-5; Sy = 0.15 понадобится, если перейти к unconfined-модели с iconvert=1.
как увидеть ugradient downgradient?
Thought for 7s
upgradient и downgradient — это две точки наблюдения относительно направления потока.
В твоей модели:
CHD слева = 10 м
CHD справа = 0 м
Значит напор выше слева, ниже справа, и поток идет примерно:
слева → направо
10 м → 0 м
Поэтому:
h_upgradient   = выше по потоку, слева от скважины
h_center       = в центре, на скважине
h_downgradient = ниже по потоку, справа от скважины
В скрипте они заданы так:
h_center       = layer 0, row 5, col 5
h_upgradient   = layer 0, row 5, col 2
h_downgradient = layer 0, row 5, col 8
То есть все три точки лежат на одной строке row=5, но в разных столбцах:
col 0        col 2        col 5        col 8        col 9
CHD=10       upgradient   center       downgradient CHD=0
|------------|------------|------------|------------|
слева                                                  справа
В ModelMuse это может отображаться как номера с 1, тогда:
h_upgradient   ≈ row 6, column 3
h_center       ≈ row 6, column 6
h_downgradient ≈ row 6, column 9
Как увидеть их наглядно
Вариант 1 — открыть CSV
Открой файл:
models/mf6/08_observations_csv/head_observations.csv
Там должны быть колонки примерно такие:
time, H_CENTER, H_UPGRADIENT, H_DOWNGRADIENT
Это самый простой способ увидеть временные ряды трех точек.
Вариант 2 — открыть готовый график
Открой:
models/mf6/08_observations_csv/observations_timeseries.png
На графике должны быть три линии:
h_center
h_upgradient
h_downgradient
Ожидаемо:
•	h_upgradient будет ближе к левому высокому напору; 
•	h_downgradient будет ближе к правому низкому напору; 
•	h_center сильнее всего реагирует на откачку, потому что там скважина. 
Вариант 3 — добавить карту с точками
Добавь такой маленький скрипт, например:
scripts/plot_b8_observation_points.py
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WS = PROJECT_ROOT / "models" / "mf6" / "08_observations_csv"

nrow, ncol = 10, 10

points = {
    "h_upgradient": (5, 2),
    "h_center / WEL": (5, 5),
    "h_downgradient": (5, 8),
}

fig, ax = plt.subplots(figsize=(7, 6), dpi=140)

# Простая сетка
ax.imshow(np.zeros((nrow, ncol)), origin="upper", alpha=0.15)

# Линии сетки
ax.set_xticks(np.arange(-0.5, ncol, 1), minor=True)
ax.set_yticks(np.arange(-0.5, nrow, 1), minor=True)
ax.grid(which="minor", linewidth=0.8)

# Номера строк/столбцов FloPy
ax.set_xticks(np.arange(ncol))
ax.set_yticks(np.arange(nrow))
ax.set_xlabel("Column, FloPy index")
ax.set_ylabel("Row, FloPy index")

# Границы CHD
ax.text(0, -0.9, "CHD = 10", ha="center", va="center")
ax.text(9, -0.9, "CHD = 0", ha="center", va="center")
ax.annotate(
    "flow direction",
    xy=(8.5, 1),
    xytext=(1, 1),
    arrowprops=dict(arrowstyle="->", lw=2),
    ha="center",
)

# Точки наблюдений
for name, (row, col) in points.items():
    ax.scatter(col, row, s=120, marker="x")
    ax.text(col, row + 0.35, name, ha="center", va="bottom", fontsize=9)

ax.set_title("B8 observation points: upgradient / center / downgradient")
ax.set_xlim(-0.5, 9.5)
ax.set_ylim(9.5, -1.2)

fig.tight_layout()
fig.savefig(WS / "b8_observation_points_map.png")
plt.close(fig)

print(WS / "b8_observation_points_map.png")
Запусти:
python scripts/plot_b8_observation_points.py
Получишь картинку:
models/mf6/08_observations_csv/b8_observation_points_map.png
Главная идея: upgradient = слева от скважины, ближе к CHD=10; downgradient = справа от скважины, ближе к CHD=0.

