from datetime import date, timedelta

import pendulum
from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator

from scripts.extract import run as extract_and_load


@dag(
    dag_id="sales_pipeline",
    description="Ежедневный забор продаж за предыдущий день и загрузка в raw.sales",
    schedule="0 7 * * *",
    start_date=pendulum.datetime(2026, 8, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["sales"],
)
def sales_pipeline():
    # start/end — фиксированные точки входа/выхода DAG'а. Сами по себе ничего не
    # делают, но дают стабильный task_id для внешних зависимостей (например,
    # ExternalTaskSensor из другого DAG'а) и единое место, куда в следующих шагах
    # повесим логирование в pipeline_runs и Telegram-алерт — независимо от того,
    # сколько реальных задач будет между ними.
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    @task
    def extract_and_load_task(ds: str = None) -> int:
        return extract_and_load(date.fromisoformat(ds))

    start >> extract_and_load_task() >> end


sales_pipeline()
