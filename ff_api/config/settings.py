from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Cache Settings
    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_ENTRIES: int = 500

    # API Settings
    OB_VERSION: str = "OB52"
    SERVER_PORT: int = 8080
    LOG_LEVEL: str = "INFO"

    # Rate Limiting
    RATE_LIMIT_RPM: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# ── AES-128-CBC constants ────────────────────────────────────
# Extracted from Free Fire APK binary (community-verified)
# Both values are 16 bytes → AES-128
# Update here if Garena rotates keys on a future OB update
AES_KEY: bytes = b"Yg&tc%DEuh6%Zc^8"
AES_IV:  bytes = b"6oyZDr22E3ychjM%"
