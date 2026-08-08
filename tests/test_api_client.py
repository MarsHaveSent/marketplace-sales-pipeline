from datetime import date

import pytest

from scripts.common import api_client


def test_fetch_day_returns_records(requests_mock):
    requests_mock.get(api_client.API_BASE_URL, json=[{"client_id": 1}])
    records = api_client.fetch_day(date(2023, 1, 15))
    assert records == [{"client_id": 1}]


def test_fetch_day_rejects_dates_before_earliest():
    with pytest.raises(api_client.ApiDateOutOfRangeError):
        api_client.fetch_day(date(2021, 12, 31))


def test_fetch_day_raises_on_non_json_response(requests_mock):
    requests_mock.get(
        api_client.API_BASE_URL,
        text="Информация за более ранние периоды отсутствует",
    )
    with pytest.raises(api_client.ApiResponseError):
        api_client.fetch_day(date(2023, 1, 15))


def test_fetch_day_raises_on_unexpected_shape(requests_mock):
    requests_mock.get(api_client.API_BASE_URL, json={"unexpected": "dict"})
    with pytest.raises(api_client.ApiResponseError):
        api_client.fetch_day(date(2023, 1, 15))
