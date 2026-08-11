from scripts.common import telegram


def test_send_alert_skips_without_credentials(monkeypatch, requests_mock):
    monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", None)
    monkeypatch.setattr(telegram.config, "TELEGRAM_CHAT_ID", None)
    telegram.send_alert("test")
    assert requests_mock.call_count == 0


def test_send_alert_posts_to_telegram_api(monkeypatch, requests_mock):
    monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setattr(telegram.config, "TELEGRAM_CHAT_ID", "42")
    requests_mock.post(
        "https://api.telegram.org/bot123:abc/sendMessage", json={"ok": True}
    )

    telegram.send_alert("test message")

    assert requests_mock.call_count == 1
    assert requests_mock.last_request.json() == {
        "chat_id": "42",
        "text": "test message",
    }
