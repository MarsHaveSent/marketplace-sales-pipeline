import argparse
import concurrent.futures
import logging
import sys
from datetime import date, datetime, timedelta, timezone

from scripts.common import api_client, db

logger = logging.getLogger(__name__)

DEFAULT_CONCURRENCY = 5


def already_loaded_dates(conn) -> set[date]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source_date FROM ops.pipeline_runs "
            "WHERE dag_run_id LIKE 'backfill__%%' AND status = 'success'"
        )
        return {row[0] for row in cur.fetchall()}


def backfill_one(target_date: date) -> None:
    conn = db.get_connection()
    started_at = datetime.now(timezone.utc)
    dag_run_id = f"backfill__{target_date.isoformat()}"
    try:
        records = api_client.fetch_day(target_date)
        loaded = db.replace_day(conn, target_date, records)
        db.log_pipeline_run(
            conn,
            dag_run_id=dag_run_id,
            source_date=target_date,
            status="success",
            rows_loaded=loaded,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )
        logger.info("%s: загружено %d записей", target_date, loaded)
    except Exception as exc:
        db.log_pipeline_run(
            conn,
            dag_run_id=dag_run_id,
            source_date=target_date,
            status="failed",
            rows_loaded=None,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            error_message=str(exc),
        )
        logger.error("%s: ошибка — %s", target_date, exc)
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Разовый забор истории с earliest даты по вчера"
    )
    parser.add_argument(
        "--start", type=str, default=api_client.EARLIEST_VALID_DATE.isoformat()
    )
    parser.add_argument(
        "--end", type=str, default=None, help="YYYY-MM-DD, по умолчанию — вчера"
    )
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    args = parse_args()
    start_date = date.fromisoformat(args.start)
    end_date = (
        date.fromisoformat(args.end) if args.end else date.today() - timedelta(days=1)
    )

    conn = db.get_connection()
    db.ensure_schema(conn)
    done = already_loaded_dates(conn)
    conn.close()

    all_dates = [
        start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)
    ]
    pending = [d for d in all_dates if d not in done]
    logger.info(
        "всего дат: %d, уже загружено: %d, осталось: %d",
        len(all_dates),
        len(done),
        len(pending),
    )

    # delete+insert в replace_day на дату не конфликтует с параллельными потоками —
    # каждый поток обрабатывает свою дату отдельным соединением
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=args.concurrency
    ) as executor:
        list(executor.map(backfill_one, pending))

    logger.info("бэкфилл завершён")


if __name__ == "__main__":
    main()
