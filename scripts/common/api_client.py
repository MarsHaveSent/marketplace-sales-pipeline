import logging
import time
from datetime import date

import requests

from scripts.common.config import API_BASE_URL

logger = logging.getLogger(__name__)

EARLIEST_VALID_DATE = date(2022, 1, 1)
REQUEST_TIMEOUT_SECONDS = 90
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 10


class ApiDateOutOfRangeError(ValueError):
    pass


class ApiResponseError(RuntimeError):
    pass


def fetch_day(target_date: date) -> list[dict]:
    """Забирает все записи за один день. API сам не валидирует дату и не
    отвечает корректным Content-Type, поэтому проверка диапазона даты и формы
    ответа лежит здесь (детали — в docs/api_notes.md)."""
    if target_date < EARLIEST_VALID_DATE:
        raise ApiDateOutOfRangeError(
            f"{target_date} is before the earliest available date {EARLIEST_VALID_DATE}"
        )

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                API_BASE_URL,
                params={"date": target_date.isoformat()},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "attempt %d/%d failed for %s: %s",
                attempt,
                MAX_ATTEMPTS,
                target_date,
                exc,
            )
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)
    else:
        raise ApiResponseError(
            f"request failed after {MAX_ATTEMPTS} attempts"
        ) from last_error

    try:
        payload = response.json()
    except ValueError as exc:
        raise ApiResponseError(
            f"non-JSON response for {target_date}: {response.text[:200]!r}"
        ) from exc

    if not isinstance(payload, list):
        raise ApiResponseError(
            f"unexpected response shape for {target_date}: {payload!r:.200}"
        )

    return payload
