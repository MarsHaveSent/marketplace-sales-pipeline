from datetime import date, timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

from scripts.common.pipeline_logging import log_pipeline_run
from scripts.extract import run as extract_and_load


def extract_and_load_task(ds: str, **_context) -> int:
    return extract_and_load(date.fromisoformat(ds))


dag = DAG(
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

# start/end — стабильный task_id для внешних зависимостей (например,
# ExternalTaskSensor) и общая точка логирования в ops.pipeline_runs
# независимо от числа реальных тасок между ними.
start = EmptyOperator(task_id="start", dag=dag)

extract_task = PythonOperator(
    task_id="extract_and_load_task",
    python_callable=extract_and_load_task,
    dag=dag,
)

dbt_run_task = BashOperator(
    task_id="dbt_run",
    bash_command="cd /opt/airflow/dbt && dbt run",
    dag=dag,
)

dbt_test_task = BashOperator(
    task_id="dbt_test",
    bash_command="cd /opt/airflow/dbt && dbt test",
    dag=dag,
)

# on_success_callback здесь, а не DAG-level: DAG-level колбэки в Airflow
# ненадёжны (apache/airflow#18113), не сработали ни разу при проверке.
# trigger_rule="all_done" — end выполняется независимо от исхода тасок выше по графу.
end = EmptyOperator(
    task_id="end",
    trigger_rule="all_done",
    on_success_callback=log_pipeline_run,
    dag=dag,
)

start >> extract_task >> dbt_run_task >> dbt_test_task >> end
