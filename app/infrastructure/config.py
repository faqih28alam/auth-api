from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_SECRETS = {
    "change-me",
    "changeme",
    "secret",
    "change-me-to-a-long-random-string",
}

DEFAULT_ADMIN_PASSWORD = "Admin123"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"
    mongodb_uri: str = "mongodb://auth:authpass@localhost:27017/auth?authSource=admin"
    mongodb_db: str = "auth"
    jwt_secret: str = "change-me-to-a-long-random-string"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000"
    trusted_hosts: str = "localhost,127.0.0.1"
    admin_username: str = "Admin"
    admin_password: str = DEFAULT_ADMIN_PASSWORD
    admin_email: str = "admin@example.com"
    web_concurrency: int = 1

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [item.strip() for item in self.trusted_hosts.split(",") if item.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


def ensure_production_safe(settings: Settings) -> None:
    if not settings.is_production:
        return
    secret = settings.jwt_secret.strip()
    if len(secret) < 32 or secret.lower() in _PLACEHOLDER_SECRETS:
        raise RuntimeError(
            "JWT_SECRET is not safe for production. Set a random value of at least 32 characters."
        )
    if "@" not in settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI must include credentials in production.")
    if not settings.cors_origin_list or "*" in settings.cors_origin_list:
        raise RuntimeError("CORS_ORIGINS must be an explicit allowlist in production.")
    if not settings.trusted_host_list or "*" in settings.trusted_host_list:
        raise RuntimeError("TRUSTED_HOSTS must be an explicit allowlist in production.")
