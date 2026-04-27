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
