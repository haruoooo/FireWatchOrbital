"""
Pydantic models e schemas para validação de dados.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FireData(BaseModel):
    """Modelo de dados de foco de queimada."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "latitude": -15.5,
                "longitude": -47.5,
                "brightness": 350.0,
                "scan": 1.5,
                "track": 1.2,
                "acq_date": "2026-06-02",
                "acq_time": "1430",
                "satellite": "NOAA-20",
                "frp": 150.5,
                "confidence": "high",
                "biome": "Cerrado",
                "state": "GO",
                "source": "nasa_firms",
                "alert_level": "high"
            }
        }
    )
    
    id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    brightness: float
    scan: float
    track: float
    acq_date: str
    acq_time: str
    satellite: str
    frp: float
    confidence: str = Field(..., pattern="^(low|nominal|high)$")
    biome: str
    state: str
    source: str
    alert_level: Optional[str] = None


class FiresResponse(BaseModel):
    """Resposta da API de focos de queimada."""
    total: int
    data_source: str
    period_days: int
    fires: list[FireData]
    updated_at: str


class StatsResponse(BaseModel):
    """Resposta com estatísticas agregadas."""
    total_fires: int
    data_source: str
    avg_frp: float
    max_frp: float
    critical_count: int
    high_count: int
    by_biome: dict[str, int]
    by_alert: dict[str, int]
    by_satellite: dict[str, int]
    top_states: dict[str, int]
    by_day: dict[str, int]
    updated_at: str


class HealthResponse(BaseModel):
    """Resposta de health check."""
    status: str
    timestamp: str
    version: str
    nasa_key_configured: bool


class DebugResponse(BaseModel):
    """Resposta do endpoint de debug."""
    url_chamada: str
    status_http: int
    primeiros_500_chars: str
    key_configurada: bool
    error: Optional[str] = None
