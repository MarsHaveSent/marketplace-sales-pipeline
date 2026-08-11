import logging
from datetime import datetime, timezone

from scripts.common import db, email_alert

logger = logging.getLogger(__name__)


def log_pipeline_run(context) -> None:
    """on_success_callback таска `end`. Не DAG-level колбэк — те в Airflow
    ненадёжны (apache/airflow#18113) не сработали ни разу при проверке."""
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

    if status == "failed":
        try:
            email_alert.send_alert(
                subject="sales_pipeline упал",
                message=f"run_id: {dag_run.run_id}\nдата: {source_date}\n{error_message}",
            )
        except Exception:
            logger.exception("не получилось отправить алерт на почту")

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
