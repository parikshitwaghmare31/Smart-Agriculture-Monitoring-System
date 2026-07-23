"""
Unit tests for the irrigation alert service: message building (English and
Marathi) and graceful behavior when Twilio isn't configured. Doesn't test
actual Twilio API calls (that would require real credentials/network) —
covers the logic that's testable in isolation.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.alert_service import AlertService, build_irrigation_alert_message


def test_english_message_includes_device_label():
    msg = build_irrigation_alert_message("North Field Plot A", None, None, language="en")
    assert "North Field Plot A" in msg
    assert "Irrigation Alert" in msg


def test_english_message_includes_water_and_duration_when_given():
    msg = build_irrigation_alert_message("Field A", water_liters=60702.8, duration_hours=3.04, language="en")
    assert "60,703" in msg or "60703" in msg
    assert "3.04" in msg


def test_marathi_message_includes_device_label():
    msg = build_irrigation_alert_message("North Field Plot A", None, None, language="mr")
    assert "North Field Plot A" in msg
    assert "सिंचन" in msg  # Marathi word for "irrigation"


def test_marathi_message_includes_water_amount():
    msg = build_irrigation_alert_message("Field A", water_liters=60702.8, duration_hours=None, language="mr")
    assert "लिटर" in msg  # Marathi word for "liters"


def test_message_without_water_or_duration_is_still_valid():
    msg = build_irrigation_alert_message("Field A", None, None, language="en")
    assert "Field A" in msg
    assert len(msg) > 0


def test_service_reports_disabled_when_alerts_not_enabled(monkeypatch):
    from app.config.settings import settings
    original = settings.ALERTS_ENABLED
    settings.ALERTS_ENABLED = False
    try:
        service = AlertService()
        service.load()
        assert service.enabled is False
    finally:
        settings.ALERTS_ENABLED = original


def test_service_reports_disabled_when_credentials_missing(monkeypatch):
    from app.config.settings import settings
    original_enabled = settings.ALERTS_ENABLED
    original_sid = settings.TWILIO_ACCOUNT_SID
    settings.ALERTS_ENABLED = True
    settings.TWILIO_ACCOUNT_SID = ""
    try:
        service = AlertService()
        service.load()
        assert service.enabled is False
    finally:
        settings.ALERTS_ENABLED = original_enabled
        settings.TWILIO_ACCOUNT_SID = original_sid


def test_send_irrigation_alert_no_ops_gracefully_when_disabled():
    service = AlertService()
    service.enabled = False
    result = service.send_irrigation_alert("+919876543210", "sms", "Test message")
    assert result["sms_sent"] is False
    assert result["whatsapp_sent"] is False
    assert result["reason"] == "alerts_not_configured"
