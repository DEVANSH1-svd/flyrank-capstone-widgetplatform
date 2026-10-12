import ipaddress
import logging

import httpx

from app.config import settings

logger = logging.getLogger("app.geo")
TIMEOUT_SECONDS = 2.0


class ProviderDown(Exception):
    pass


def _lookup_a(ip: str) -> dict:
    if settings.geo_mode == "mock":
        return {"country": "Mockland", "city": "Mock City A"}
    resp = httpx.get(
        f"http://ip-api.com/json/{ip}",
        params={"fields": "status,country,city"},
        timeout=TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "success":
        raise ProviderDown("ip-api.com reported failure")
    return {"country": data.get("country"), "city": data.get("city")}


def _lookup_b(ip: str) -> dict:
    if settings.geo_mode == "mock":
        return {"country": "Mockland", "city": "Mock City B"}
    resp = httpx.get(f"https://ipapi.co/{ip}/json/", timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise ProviderDown("ipapi.co reported an error")
    return {"country": data.get("country_name"), "city": data.get("city")}


PROVIDERS = [("a", _lookup_a), ("b", _lookup_b)]


def _is_private(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return True


def enrich(ip: str | None) -> tuple[dict | None, str | None]:
    """Return (geo data, provider name). Never raises: degrade, never fail."""
    if ip is None:
        return None, None
    if settings.geo_mode == "live" and _is_private(ip):
        return None, None  # real providers cannot locate private addresses

    down = {name.strip() for name in settings.geo_force_down.split(",") if name.strip()}
    for name, lookup in PROVIDERS:
        try:
            if name in down:
                raise ProviderDown(f"provider {name} is forced down")
            return lookup(ip), name
        except Exception as exc:  # any failure moves on to the next provider
            logger.warning("Geo provider %s failed: %s", name, exc)
    logger.warning("All geo providers failed; storing submission without geo data")
    return None, None