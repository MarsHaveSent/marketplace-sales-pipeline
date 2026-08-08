from datetime import date

import psycopg2
from psycopg2.extras import Json, execute_values

from scripts.common import config


def get_connection():
    missing = [
        name
        for name, value in [
            ("POSTGRES_DB", config.POSTGRES_DB),
            ("POSTGRES_USER", config.POSTGRES_USER),
            ("POSTGRES_PASSWORD", config.POSTGRES_PASSWORD),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(f"нет значений в .env для: {', '.join(missing)}")
    return psycopg2.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        dbname=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
    )


def ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS raw.sales (
                id BIGSERIAL PRIMARY KEY,
                source_date DATE NOT NULL,
                payload JSONB NOT NULL,
                fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_raw_sales_source_date ON raw.sales (source_date)"
        )
    conn.commit()


def replace_day(conn, target_date: date, records: list[dict]) -> int:
    """Перезаписывает данные за дату одной транзакцией: сначала удаляет
    старые строки, потом вставляет новые. У записей API нет надёжного
    бизнес-ключа для ON CONFLICT, а данные за день стабильны (see docs/api_notes.md)"""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM raw.sales WHERE source_date = %s", (target_date,))
        if records:
            execute_values(
                cur,
                "INSERT INTO raw.sales (source_date, payload) VALUES %s",
                [(target_date, Json(r)) for r in records],
            )
    conn.commit()
    return len(records)
