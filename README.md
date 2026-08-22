# Дипломный проект: аналитика продаж маркетплейса

Пайплайн данных с API маркетплейса в PostgreSQL, оркестрация в Airflow, трансформации в dbt, BI-дашборды в Metabase и Yandex DataLens.

## Поток данных

API (по одному дню за раз) → `extract.py` → `raw.sales` → dbt staging → dbt marts → Metabase / DataLens / аналитика

Ежедневный запуск в Airflow, деплой на push в main через GitHub Actions. Разбор решений — в [`docs/architecture.md`](docs/architecture.md).

## Стек

Docker · PostgreSQL · Apache Airflow · dbt · Metabase · Yandex DataLens · GitHub Actions (CI/CD) · Poetry · pytest

## Аналитика

Два исследования на данных 2023 года, оба - Jupyter-ноутбуки с кодом, графиками и выводами:

- [`01_assortment_abc_xyz.ipynb`](analysis/01_assortment_abc_xyz.ipynb) - ABC/XYZ ассортимента, эластичность спроса к скидке
- [`02_customers_ltv.ipynb`](analysis/02_customers_ltv.ipynb) - RFM-сегментация, когортный анализ retention

Плюс [`00_pygwalker_eda.ipynb`](analysis/00_pygwalker_eda.ipynb) - разведка перед тем как фиксировать гипотезы.

Выводы проверены на цифрах: классическая граница ABC 80/20 в этих данных не подтвердилась (нужно 53% товаров, не 20%), скидка на продажи не влияет вообще (корреляция 0.0004).

## Структура репозитория

```
.github/workflows/  — CI (lint + тесты) и CD (деплой на сервер)
infra/               — docker-compose.yml, Dockerfile для Airflow, .env.example
dags/                — Airflow DAG пайплайна
dbt/                 — dbt-проект: staging → marts
scripts/             — extract / load / backfill + общий код (API-клиент, логирование, алерты)
tests/               — pytest
analysis/            — Jupyter-ноутбуки с исследованиями
docs/                — архитектура, инструкция по разворачиванию, заметки по API
```

## Лицензия

MIT, см. [LICENSE](LICENSE).
