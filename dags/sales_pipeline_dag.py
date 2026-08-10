from datetime import date, timedelta

import pendulum
from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator

from scripts.common.pipeline_logging import log_pipeline_run
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
    # start/end — фиксированные точки входа/выхода DAG'а: стабильный task_id для
    # внешних зависимостей (например, ExternalTaskSensor из другого DAG'а) и
    # единое место логирования в ops.pipeline_runs, независимо от того, сколько
    # реальных задач будет между ними (в Неделе 3 сюда добавятся dbt run/test).
    # Логирование — на on_success_callback самого `end` (см. pipeline_logging.py),
    # а не на DAG-level колбэках: те в Airflow ненадёжны (apache/airflow#18113),
    # ни разу не сработали при проверке. trigger_rule="all_done" — end
    # выполняется независимо от исхода extract_and_load_task.
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(
        task_id="end",
        trigger_rule="all_done",
        on_success_callback=log_pipeline_run,
    )

    @task
    def extract_and_load_task(ds: str = None) -> int:
        return extract_and_load(date.fromisoformat(ds))

    start >> extract_and_load_task() >> end


sales_pipeline()
