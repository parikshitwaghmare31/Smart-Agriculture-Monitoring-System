"""
Irrigation alert service — sends SMS and/or WhatsApp notifications via
Twilio when the system determines a field needs irrigation.

Honesty note on WhatsApp: Twilio's WhatsApp Business API, for personal/demo
use, runs through their free "sandbox" number. Each recipient must first
send a one-time join code (e.g. "join <code-word>") to that sandbox number
from their own WhatsApp before they can receive messages — a real
limitation for farmers without smartphones, since joining itself requires
WhatsApp. SMS has no such limitation and works on any phone, including
basic feature phones, so it's the more universally reliable channel here.

Gracefully degrades to a no-op (with a clear log message) if Twilio
credentials aren't configured, rather than crashing the app — alerting is
an enhancement, not a dependency the core system should ever be blocked on.
"""

from datetime import datetime, timezone, timedelta

from app.config.settings import settings
from app.config.logging_config import app_logger


class AlertService:
    def __init__(self):
        self.client = None
        self.enabled = False

    def load(self):
        if not settings.ALERTS_ENABLED:
            app_logger.info("SMS/WhatsApp alerts disabled (ALERTS_ENABLED=false)")
            self.enabled = False
            return

        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            app_logger.warning(
                "ALERTS_ENABLED=true but TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN are not set — "
                "alerts will not be sent. Configure them to enable this feature."
            )
            self.enabled = False
            return

        try:
            from twilio.rest import Client
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            self.enabled = True
            app_logger.info("Alert service initialized (Twilio)")
        except ImportError:
            app_logger.error("twilio package not installed — cannot send SMS/WhatsApp alerts")
            self.enabled = False

    def _send_sms(self, to_number: str, message: str) -> bool:
        if not settings.TWILIO_SMS_FROM_NUMBER:
            app_logger.warning("TWILIO_SMS_FROM_NUMBER not configured — cannot send SMS")
            return False
        try:
            self.client.messages.create(
                body=message, from_=settings.TWILIO_SMS_FROM_NUMBER, to=to_number
            )
            return True
        except Exception as e:
            app_logger.error(f"Failed to send SMS to {to_number}: {e}")
            return False

    def _send_whatsapp(self, to_number: str, message: str) -> bool:
        if not settings.TWILIO_WHATSAPP_FROM_NUMBER:
            app_logger.warning("TWILIO_WHATSAPP_FROM_NUMBER not configured — cannot send WhatsApp message")
            return False
        try:
            self.client.messages.create(
                body=message,
                from_=settings.TWILIO_WHATSAPP_FROM_NUMBER,
                to=f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number,
            )
            return True
        except Exception as e:
            app_logger.error(f"Failed to send WhatsApp message to {to_number}: {e}")
            return False

    def send_irrigation_alert(self, phone_number: str, channel: str, message: str) -> dict:
        """
        Sends the alert on the requested channel(s). Returns a dict of
        which channels were actually attempted and whether each succeeded,
        so the caller can log a precise record rather than a single bool.
        """
        if not self.enabled:
            app_logger.info(
                f"Alert service not enabled — would have sent to {phone_number}: {message}"
            )
            return {"sms_sent": False, "whatsapp_sent": False, "reason": "alerts_not_configured"}

        result = {"sms_sent": False, "whatsapp_sent": False}

        if channel in ("sms", "both"):
            result["sms_sent"] = self._send_sms(phone_number, message)
        if channel in ("whatsapp", "both"):
            result["whatsapp_sent"] = self._send_whatsapp(phone_number, message)

        return result


def build_irrigation_alert_message(
    device_label: str, water_liters: float | None, duration_hours: float | None, language: str = "en"
) -> str:
    """
    Builds a short, SMS-friendly alert message in the farmer's preferred
    language. Kept deliberately short and plain — no emoji/markdown, since
    basic feature phones and SMS gateways don't render those reliably.
    """
    if language == "mr":
        msg = f"सिंचन सूचना: {device_label} साठी पाणी देण्याची गरज आहे."
        if water_liters:
            msg += f" अंदाजे {round(water_liters):,} लिटर पाणी लागेल."
        if duration_hours:
            msg += f" पंप अंदाजे {duration_hours} तास चालवा."
        return msg

    msg = f"Irrigation Alert: {device_label} needs watering."
    if water_liters:
        msg += f" Approx {round(water_liters):,} liters needed."
    if duration_hours:
        msg += f" Run pump for approx {duration_hours} hours."
    return msg


async def should_send_alert(db, device_id: str) -> bool:
    """
    Enforces a cooldown period so the same device doesn't spam a farmer
    with repeat alerts every time a new sensor reading confirms the same
    ongoing dry condition. Checks the alert log for this device's most
    recent SUCCESSFUL alert timestamp — a failed attempt (e.g. Twilio
    wasn't configured yet at the time) must never block a future retry,
    since nothing was actually delivered to the farmer.
    """
    last_successful_alert = await db[settings.ALERT_LOG_COLLECTION].find_one(
        {
            "device_id": device_id,
            "$or": [{"sms_sent": True}, {"whatsapp_sent": True}],
        },
        sort=[("timestamp", -1)],
    )
    if not last_successful_alert:
        return True

    cooldown_cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.ALERT_COOLDOWN_HOURS)
    last_timestamp = last_successful_alert["timestamp"]
    if last_timestamp.tzinfo is None:
        last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)

    return last_timestamp < cooldown_cutoff


async def check_and_send_irrigation_alert(db, reading: dict):
    """
    Shared entry point used by BOTH the MQTT ingestion path and the REST
    /sensor-data POST path: runs the same ML prediction the manual
    dashboard button uses, and if irrigation is recommended AND the
    farmer has opted into alerts AND the cooldown period has elapsed,
    sends an SMS/WhatsApp notification. Any failure here is logged but
    never allowed to break sensor ingestion itself — alerting is an
    enhancement, not a dependency the core pipeline should ever be blocked on.
    """
    try:
        from app.services.ml_service import ml_service
        from app.services.irrigation_area_utils import compute_total_water_needed

        device_id = reading.get("device_id", "unknown")

        if not ml_service.loaded and not alert_service.enabled:
            app_logger.debug(f"Alert check skipped for {device_id}: ML model not loaded and alerts not enabled")
            return

        irrigate, confidence, water_amount, _ = ml_service.predict(
            reading["soil_moisture"], reading["temperature"], reading["humidity"]
        )
        if not irrigate:
            app_logger.debug(f"Alert check for {device_id}: irrigation not needed (irrigate=False), no alert sent")
            return

        device = await db[settings.DEVICE_COLLECTION].find_one({"device_id": device_id})
        if not device:
            app_logger.info(
                f"Alert check for {device_id}: irrigation needed but device is not registered "
                f"(no entry in devices collection) — cannot determine an owner to notify"
            )
            return

        farmer = await db[settings.USER_COLLECTION].find_one({"email": device["owner_email"]})
        if not farmer:
            app_logger.warning(
                f"Alert check for {device_id}: registered owner_email "
                f"'{device['owner_email']}' has no matching user account"
            )
            return
        if not farmer.get("alerts_enabled"):
            app_logger.info(
                f"Alert check for {device_id}: owner {farmer['email']} has not enabled alerts, skipping"
            )
            return
        if not farmer.get("phone_number"):
            app_logger.info(
                f"Alert check for {device_id}: owner {farmer['email']} has alerts enabled but no phone number set"
            )
            return

        if not await should_send_alert(db, device_id):
            app_logger.info(f"Alert check for {device_id}: still within cooldown period, skipping")
            return

        app_logger.info(
            f"Alert check for {device_id}: all conditions met, sending alert to {farmer['email']}"
        )

        total_liters = None
        duration_hours = None
        if device.get("area_value"):
            area_info = compute_total_water_needed(
                water_depth_liters_per_sqm=water_amount,
                area_value=device["area_value"],
                area_unit=device.get("area_unit", "acre"),
                flow_rate_lph=device.get("flow_rate_lph"),
            )
            total_liters = area_info["total_liters_needed"]
            duration_hours = area_info["recommended_duration_hours"]

        message = build_irrigation_alert_message(
            device_label=device.get("label", reading["device_id"]),
            water_liters=total_liters,
            duration_hours=duration_hours,
            language=farmer.get("preferred_language", "en"),
        )

        result = alert_service.send_irrigation_alert(
            phone_number=farmer["phone_number"],
            channel=farmer.get("alert_channel", "sms"),
            message=message,
        )

        await db[settings.ALERT_LOG_COLLECTION].insert_one({
            "device_id": reading["device_id"],
            "owner_email": device["owner_email"],
            "message": message,
            "timestamp": datetime.now(timezone.utc),
            **result,
        })
        app_logger.info(f"Irrigation alert sent for device {reading['device_id']}: {result}")

    except Exception as e:
        app_logger.error(f"Irrigation alert check failed for {reading.get('device_id')}: {e}")


alert_service = AlertService()
