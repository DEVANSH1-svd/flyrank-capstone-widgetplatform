from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables or the .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    public_base_url: str = "http://127.0.0.1:8000"

    # Rate limiting (token bucket: burst size, then tokens refilled per second)
    rate_limit_ip_burst: int = 10
    rate_limit_ip_per_second: float = 1.0
    rate_limit_widget_burst: int = 100
    rate_limit_widget_per_second: float = 5.0

    # Geo enrichment: "live" calls the real providers, "mock" returns fixed data.
    # geo_force_down lists providers to treat as unavailable, e.g. "a" or "a,b".
    geo_mode: str = "live"
    geo_force_down: str = ""

    # Confirmation email side effect (logged to the console, not really sent)
    email_force_fail: bool = False
    email_retry_delay_seconds: float = 1.0


settings = Settings()