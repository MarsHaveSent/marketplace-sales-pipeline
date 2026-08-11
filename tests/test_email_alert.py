from unittest.mock import MagicMock, patch

from scripts.common import email_alert


def test_send_alert_skips_without_credentials(monkeypatch):
    monkeypatch.setattr(email_alert.config, "SMTP_USER", None)
    monkeypatch.setattr(email_alert.config, "SMTP_PASSWORD", None)
    with patch("smtplib.SMTP_SSL") as smtp_cls:
        email_alert.send_alert("subject", "body")
    smtp_cls.assert_not_called()


def test_send_alert_sends_via_smtp(monkeypatch):
    monkeypatch.setattr(email_alert.config, "SMTP_USER", "bot@mail.ru")
    monkeypatch.setattr(email_alert.config, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(email_alert.config, "ALERT_EMAIL_TO", "me@mail.ru")

    smtp_instance = MagicMock()
    smtp_instance.__enter__.return_value = smtp_instance
    with patch("smtplib.SMTP_SSL", return_value=smtp_instance) as smtp_cls:
        email_alert.send_alert("subject", "body")

    smtp_cls.assert_called_once_with(
        email_alert.config.SMTP_HOST, email_alert.config.SMTP_PORT
    )
    smtp_instance.login.assert_called_once_with("bot@mail.ru", "secret")
    sent_message = smtp_instance.send_message.call_args[0][0]
    assert sent_message["To"] == "me@mail.ru"
    assert sent_message["Subject"] == "subject"
