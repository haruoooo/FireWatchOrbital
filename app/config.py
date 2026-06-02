"""
Configuração centralizada da aplicação usando Pydantic Settings.
"""
import logging
from pathlib import Path
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação FireWatch Orbital."""
    
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    
    # NASA API
    nasa_api_key: str
    nasa_firms_base: str = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    
    # Application
    app_title: str = "FireWatch Orbital API"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    templates_dir: Optional[Path] = None
    static_dir: Optional[Path] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.templates_dir is None:
            self.templates_dir = self.base_dir / "templates"
        if self.static_dir is None:
            self.static_dir = self.base_dir / "static"


def get_settings() -> Settings:
    """Factory para obter configurações."""
    return Settings()


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configura logging estruturado."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )
    return logging.getLogger("firewatch")
