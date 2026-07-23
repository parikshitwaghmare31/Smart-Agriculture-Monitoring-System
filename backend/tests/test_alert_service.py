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


def test_should_send_alert_ignores_failed_previous_attempts():
    """
    Regression test for a real bug found during manual testing: an alert
    attempt that failed (e.g. Twilio wasn't configured yet at the time)
    must NOT count toward the cooldown, since nothing was actually
    delivered to the farmer. Only successful sends should start the
    cooldown clock.
    """
    import asyncio
    from unittest.mock import AsyncMock
    from app.services.alert_service import should_send_alert

    # Simulate a MongoDB collection where find_one is queried with a filter
    # that requires sms_sent or whatsapp_sent to be True. Since our fake
    # "database" only has a FAILED log entry, a correctly-filtered query
    # should find nothing and return None, allowing a fresh send.
    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value=None)  # no successful attempt exists
    mock_db = {"irrigation_alerts_log": mock_collection}

    result = asyncio.run(should_send_alert(mock_db, "esp32-field-04"))
    assert result is True

    # Confirm the query actually filters on success, not just device_id
    called_filter = mock_collection.find_one.call_args[0][0]
    assert "$or" in called_filter
    assert {"sms_sent": True} in called_filter["$or"]
    assert {"whatsapp_sent": True} in called_filter["$or"]
