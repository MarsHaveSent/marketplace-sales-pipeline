from datetime import datetime, timezone

from scripts.common import db


def _log(context, status: str) -> None:
    """Общий колбэк для on_success_callback/on_failure_callback на уровне DAG:
    пишет одну строку в ops.pipeline_runs на весь прогон, независимо от того,
    сколько тасок внутри DAG'а"""
    dag_run = context["dag_run"]
    source_date = dag_run.execution_date.date()

    extract_ti = dag_run.get_task_instance(task_id="extract_and_load_task")
    rows_loaded = (
        extract_ti.xcom_pull(task_ids="extract_and_load_task") if extract_ti else None
    )

    error_message = None
    if status == "failed":
        failed_tasks = [
            ti.task_id for ti in dag_run.get_task_instances() if ti.state == "failed"
        ]
        if failed_tasks:
            error_message = f"failed tasks: {', '.join(failed_tasks)}"

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


def log_success(context) -> None:
    _log(context, status="success")


def log_failure(context) -> None:
    _log(context, status="failed")
