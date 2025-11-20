from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    APP_NAME: str = "Cafetería API"
    APP_VERSION: str = "1.0.0"

    # Selección del backend de repositorio: memory | file | database
    REPO_BACKEND: Literal["memory", "file", "database"] = "memory"
    
    # Configuración del Circuit Breaker (opcional)
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: float = 30.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
