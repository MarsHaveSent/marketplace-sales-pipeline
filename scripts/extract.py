import argparse
import logging
import sys
from datetime import date, timedelta

from scripts.common import api_client, db

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Забрать данные за один день и загрузить в raw.sales"
    )
    parser.add_argument(
        "--date", type=str, default=None, help="YYYY-MM-DD, по умолчанию — вчера"
    )
    return parser.parse_args()


def run(target_date: date) -> int:
    """Забрать один день и загрузить в raw.sales. Вызывается и из CLI (main),
    и из Airflow DAG (dags/sales_pipeline_dag.py) — логика одна, входная точка разная.
    """
    logger.info("забираю данные за %s", target_date)
    records = api_client.fetch_day(target_date)
    logger.info("получено %d записей за %s", len(records), target_date)

    conn = db.get_connection()
    try:
        db.ensure_schema(conn)
        loaded = db.replace_day(conn, target_date, records)
        logger.info("загружено %d записей в raw.sales за %s", loaded, target_date)
        return loaded
    finally:
        conn.close()


def main() -> None:
    # На Windows-консоли кодировка по умолчанию не utf-8; актуально только для CLI-запуска.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    args = parse_args()
    target_date = (
        date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    )
    run(target_date)


if __name__ == "__main__":
    main()
