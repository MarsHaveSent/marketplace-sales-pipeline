# Дипломный проект: аналитика продаж маркетплейса

Пайплайн данных с API маркетплейса в PostgreSQL, оркестрация в Airflow, трансформации в dbt, BI-дашборды в Metabase и Yandex DataLens — плюс два аналитических исследования (оптимизация ассортимента, работа с клиентской базой/LTV).

Разбор архитектурных решений — в [`docs/architecture.md`](docs/architecture.md).

## Стек

Docker · PostgreSQL · Apache Airflow · dbt · Metabase · Yandex DataLens · GitHub Actions (CI/CD) · Poetry · pytest

## Структура репозитория

```
.github/workflows/  — CI (lint + тесты) и CD (деплой на сервер)
infra/               — docker-compose.yml, Dockerfile для Airflow, .env.example
dags/                — Airflow DAG пайплайна
dbt/                 — dbt-проект: staging → marts
scripts/             — extract / load / backfill + общий код (API-клиент, логирование, алерты)
tests/               — pytest
analysis/            — Jupyter-ноутбуки с исследованиями + экспорт в HTML/PDF
docs/                — архитектура, инструкция по разворачиванию, заметки по API
```
