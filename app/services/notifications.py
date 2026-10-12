import logging
import time

from app.config import settings

logger = logging.getLogger("app.notifications")


def send_email(to: str, subject: str, body: str) -> None:
    """Pretend to send an email by logging it. Can be forced to fail for testing."""
    if settings.email_force_fail:
        raise RuntimeError("Email provider unavailable (forced failure)")
    logger.info("EMAIL to=%s subject=%s", to, subject)


def send_confirmation(to: str, widget_title: str, attempts: int = 3) -> None:
    """Background job: retry a few times, then log an ALERT. Never raises."""
    subject = f"Thanks for your submission to {widget_title}"
    for attempt in range(1, attempts + 1):
        try:
            send_email(to, subject, "We received your submission.")
            return
        except Exception as exc:
            logger.warning("Email attempt %d/%d failed: %s", attempt, attempts, exc)
            if attempt < attempts:
                time.sleep(settings.email_retry_delay_seconds)
    logger.error("ALERT: confirmation email failed after %d attempts", attempts)