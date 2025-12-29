"""Configurações do SDK carregadas de variáveis de ambiente"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class SankhyaSettings(BaseSettings):
    """Configurações da conexão Sankhya"""

    url: str = Field(default="http://localhost", alias="SANKHYA_URL")
    port: int = Field(default=8180, alias="SANKHYA_PORT")
    username: str = Field(..., alias="SANKHYA_USERNAME")
    password: str = Field(..., alias="SANKHYA_PASSWORD")
    key_path: Optional[str] = Field(default=None, alias="SANKHYA_KEY_PATH")
    appkey: Optional[str] = Field(default=None, alias="SANKHYA_APPKEY")
    token: Optional[str] = Field(default=None, alias="SANKHYA_TOKEN")
    timeout: int = Field(default=30, alias="SANKHYA_TIMEOUT")
    max_retries: int = Field(default=3, alias="SANKHYA_MAX_RETRIES")
    log_level: str = Field(default="INFO", alias="SANKHYA_LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Instância global de configurações
try:
    settings = SankhyaSettings()
except Exception:
    # Fallback para quando o .env não está presente ou incompleto durante o build/test
    # Em produção, as variáveis de ambiente devem estar configuradas
    import os
    settings = SankhyaSettings(
        SANKHYA_USERNAME=os.getenv("SANKHYA_USERNAME", "placeholder"),
        SANKHYA_PASSWORD=os.getenv("SANKHYA_PASSWORD", "placeholder")
    )
