from datetime import date, datetime, timezone

import pytest

from scripts.common import db

TEST_DATE = date(1999, 1, 1)


@pytest.fixture
def conn():
    connection = db.get_connection()
    db.ensure_schema(connection)
    yield connection
    with connection.cursor() as cur:
        cur.execute("DELETE FROM raw.sales WHERE source_date = %s", (TEST_DATE,))
        cur.execute("DELETE FROM ops.pipeline_runs WHERE dag_run_id LIKE 'pytest-%%'")
    connection.commit()
    connection.close()


def test_replace_day_inserts_records(conn):
    loaded = db.replace_day(conn, TEST_DATE, [{"a": 1}, {"a": 2}])
    assert loaded == 2

    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM raw.sales WHERE source_date = %s", (TEST_DATE,)
        )
        assert cur.fetchone()[0] == 2


def test_replace_day_overwrites_existing(conn):
    db.replace_day(conn, TEST_DATE, [{"a": 1}, {"a": 2}, {"a": 3}])
    db.replace_day(conn, TEST_DATE, [{"a": 9}])

    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM raw.sales WHERE source_date = %s", (TEST_DATE,)
        )
        assert cur.fetchone()[0] == 1


def test_log_pipeline_run_inserts_row(conn):
    db.log_pipeline_run(
        conn,
        dag_run_id="pytest-test-run",
        source_date=TEST_DATE,
        status="success",
        rows_loaded=5,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )

    with conn.cursor() as cur:
        cur.execute(
            "SELECT status, rows_loaded FROM ops.pipeline_runs WHERE dag_run_id = %s",
            ("pytest-test-run",),
        )
        assert cur.fetchone() == ("success", 5)
