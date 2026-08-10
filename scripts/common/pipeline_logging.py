from datetime import datetime, timezone

from scripts.common import db


def log_pipeline_run(context) -> None:
    """on_success_callback таска `end` (см. dags/sales_pipeline_dag.py).

    Висит на `end`, а не на DAG-level on_success/on_failure_callback: DAG-level
    колбэки в Airflow ненадёжны (github.com/apache/airflow/issues/18113) — на
    практике не сработали ни разу при проверке. Таск-level колбэк выполняется
    прямо в процессе воркера сразу после завершения таска и срабатывает стабильно.
    `end` запускается с trigger_rule="all_done", поэтому этот колбэк вызывается
    независимо от исхода extract_and_load_task — статус прогона определяется
    здесь же, по состояниям соседних тасок.
    """
    dag_run = context["dag_run"]
    source_date = dag_run.execution_date.date()

    extract_ti = dag_run.get_task_instance(task_id="extract_and_load_task")
    rows_loaded = (
        extract_ti.xcom_pull(task_ids="extract_and_load_task") if extract_ti else None
    )

    failed_tasks = [
        ti.task_id
        for ti in dag_run.get_task_instances()
        if ti.task_id != "end" and ti.state in ("failed", "upstream_failed")
    ]
    status = "failed" if failed_tasks else "success"
    error_message = f"failed tasks: {', '.join(failed_tasks)}" if failed_tasks else None

    conn = db.get_connection()
    try:
        db.ensure_schema(conn)
        db.log_pipeline_run(
            conn,
            dag_run_id=dag_run.run_id,
            source_date=source_date,
            status=status,
            rows_loaded=rows_loaded,
            started_at=dag_run.start_date,
            finished_at=datetime.now(timezone.utc),
            error_message=error_message,
        )
    finally:
        conn.close()
