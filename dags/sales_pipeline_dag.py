from datetime import date, timedelta

import pendulum
from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator

from scripts.common.pipeline_logging import log_failure, log_success
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
    # Колбэки на уровне DAG, а не таски — срабатывают ровно один раз на весь прогон
    # (пишут в ops.pipeline_runs см. pipeline_logging.py).
    on_success_callback=log_success,
    on_failure_callback=log_failure,
)
def sales_pipeline():
    # start/end — фиксированные точки входа/выхода DAG'а.
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    @task
    def extract_and_load_task(ds: str = None) -> int:
        return extract_and_load(date.fromisoformat(ds))

    start >> extract_and_load_task() >> end


sales_pipeline()
