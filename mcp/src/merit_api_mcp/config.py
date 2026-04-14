import os
from dataclasses import dataclass
from typing import Mapping, Optional


SUPPORTED_ENV_VARS = ("MERIT_API_ID", "MERIT_API_KEY", "MERIT_API_COUNTRY")
SUPPORTED_COUNTRIES = ("EE", "PL")


@dataclass(frozen=True)
class MeritMCPConfig:
    api_id: str
    api_key: str
    country: str = "EE"


def load_config_from_env(env: Optional[Mapping[str, str]] = None) -> Optional[MeritMCPConfig]:
    source = os.environ if env is None else env
    api_id = (source.get("MERIT_API_ID") or "").strip()
    api_key = (source.get("MERIT_API_KEY") or "").strip()
    country = (source.get("MERIT_API_COUNTRY") or "EE").strip().upper() or "EE"

    if not api_id or not api_key:
        return None

    if country not in SUPPORTED_COUNTRIES:
        country = "EE"

    return MeritMCPConfig(api_id=api_id, api_key=api_key, country=country)


def build_setup_payload(
    *,
    blocked_tool: Optional[str] = None,
    blocked_api_method: Optional[str] = None,
) -> dict:
    payload = {
        "mode": "setup",
        "error": "Merit API credentials are not configured.",
        "message": (
            "Set MERIT_API_ID and MERIT_API_KEY to enable API-backed MCP tools. "
            "MERIT_API_COUNTRY is optional and defaults to EE."
        ),
        "supported_env_vars": list(SUPPORTED_ENV_VARS),
        "supported_countries": list(SUPPORTED_COUNTRIES),
        "example": {
            "MERIT_API_ID": "your-api-id",
            "MERIT_API_KEY": "your-api-key",
            "MERIT_API_COUNTRY": "EE",
        },
    }
    if blocked_tool:
        payload["blocked_tool"] = blocked_tool
    if blocked_api_method:
        payload["blocked_api_method"] = blocked_api_method
    return payload
