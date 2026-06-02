"""
FastAPI application - FireWatch Orbital
Monitoramento de queimadas com dados orbitais da NASA FIRMS
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app.config import get_settings, setup_logging
from app.models import FiresResponse, StatsResponse, HealthResponse, DebugResponse, FireData
from app.services.nasa_firms import fetch_nasa_firms, generate_synthetic_fires
from app.services.fire_classifier import classify_alert

# Configurações
settings = get_settings()
logger = setup_logging(settings.log_level)

# FastAPI app
app = FastAPI(
    title=settings.app_title,
    description="Monitoramento de queimadas com dados orbitais da NASA FIRMS",
    version=settings.app_version,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _apply_fire_alerts(fires: list[FireData]) -> list[FireData]:
    """Adiciona nivel de alerta a cada foco."""
    for fire in fires:
        fire.alert_level = classify_alert(fire.frp)
    return fires


# ============================================================================
# ROUTES: WEB UI
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    """Retorna dashboard HTML principal."""
    try:
        content = (settings.templates_dir / "index.html").read_text(encoding="utf-8")
        return content
    except FileNotFoundError:
        return "<h1>Template index.html não encontrado</h1>"


# ============================================================================
# ROUTES: HEALTH & DEBUG
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check da aplicação."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.app_version,
        nasa_key_configured=bool(settings.nasa_api_key),
    )


@app.get("/api/debug", response_model=DebugResponse)
async def debug_nasa() -> DebugResponse:
    """
    Debug endpoint - mostra a resposta bruta da NASA FIRMS.
    Útil para diagnosticar problemas com a chave API.
    """
    if not settings.nasa_api_key:
        return DebugResponse(
            url_chamada="N/A",
            status_http=0,
            primeiros_500_chars="",
            key_configurada=False,
            error="NASA_API_KEY não está definida no .env"
        )
    
    nasa_firms_base = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    from app.constants import BRAZIL_BOUNDS
    
    url = (
        f"{nasa_firms_base}/{settings.nasa_api_key}/MODIS_NRT/"
        f"{BRAZIL_BOUNDS['min_lon']},{BRAZIL_BOUNDS['min_lat']},"
        f"{BRAZIL_BOUNDS['max_lon']},{BRAZIL_BOUNDS['max_lat']}/1"
    )
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
        return DebugResponse(
            url_chamada=url.replace(settings.nasa_api_key, "***KEY***"),
            status_http=resp.status_code,
            primeiros_500_chars=resp.text[:500],
            key_configurada=bool(settings.nasa_api_key),
        )
    except Exception as e:
        return DebugResponse(
            url_chamada="N/A",
            status_http=0,
            primeiros_500_chars="",
            key_configurada=bool(settings.nasa_api_key),
            error=str(e)
        )


# ============================================================================
# ROUTES: API - FIRES
# ============================================================================

@app.get("/api/fires", response_model=FiresResponse)
async def get_fires(
    days: int = Query(default=5, ge=1, le=5, description="Número de dias históricos"),
    confidence: Optional[str] = Query(
        default=None,
        pattern="^(low|nominal|high)$",
        description="Filtrar por nível de confiança"
    ),
    min_frp: float = Query(default=0, ge=0, description="FRP mínimo (MW)"),
) -> FiresResponse:
    """
    Retorna focos de queimada com filtros opcionais.
    
    - **days**: 1-5 dias históricos
    - **confidence**: low, nominal ou high
    - **min_frp**: Radiative power mínimo
    """
    try:
        fires = await fetch_nasa_firms(settings.nasa_api_key, days)
        if not fires:
            raise ValueError("NASA FIRMS retornou 0 focos após parsing")
        data_source = "nasa_firms"
    except Exception as e:
        logger.warning("Fallback para dados sintéticos. Motivo: %s", e)
        fires = generate_synthetic_fires(250)
        data_source = "synthetic"
    
    # Aplicar filtros
    if confidence:
        fires = [f for f in fires if f.confidence == confidence]
    if min_frp > 0:
        fires = [f for f in fires if f.frp >= min_frp]
    
    # Adicionar alert_level
    fires = _apply_fire_alerts(fires)
    
    return FiresResponse(
        total=len(fires),
        data_source=data_source,
        period_days=days,
        fires=fires,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# ROUTES: API - STATS
# ============================================================================

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Retorna estatísticas agregadas dos focos de queimada."""
    try:
        fires = await fetch_nasa_firms(settings.nasa_api_key, 5)
        if not fires:
            raise ValueError("NASA FIRMS retornou 0 focos após parsing")
        data_source = "nasa_firms"
    except Exception as e:
        logger.warning("Stats — fallback para dados sintéticos. Motivo: %s", e)
        fires = generate_synthetic_fires(250)
        data_source = "synthetic"
    
    # Adicionar alert_level
    fires = _apply_fire_alerts(fires)
    
    # Agregações
    by_biome: dict[str, int] = {}
    by_state: dict[str, int] = {}
    by_alert: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_day: dict[str, int] = {}
    by_satellite: dict[str, int] = {}
    
    for f in fires:
        biome = f.biome or "N/A"
        state = f.state or "N/A"
        alert = f.alert_level or "low"
        day = f.acq_date or ""
        sat = f.satellite or "N/A"
        
        by_biome[biome] = by_biome.get(biome, 0) + 1
        by_state[state] = by_state.get(state, 0) + 1
        by_alert[alert] = by_alert.get(alert, 0) + 1
        by_day[day] = by_day.get(day, 0) + 1
        by_satellite[sat] = by_satellite.get(sat, 0) + 1
    
    # Top 10 states
    top_states = dict(sorted(by_state.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # Days sorted
    days_sorted = dict(sorted(by_day.items()))
    
    # FRP stats
    frp_values = [f.frp for f in fires if f.frp > 0]
    avg_frp = round(sum(frp_values) / len(frp_values), 1) if frp_values else 0
    max_frp = round(max(frp_values), 1) if frp_values else 0
    
    return StatsResponse(
        total_fires=len(fires),
        data_source=data_source,
        avg_frp=avg_frp,
        max_frp=max_frp,
        critical_count=by_alert["critical"],
        high_count=by_alert["high"],
        by_biome=by_biome,
        by_alert=by_alert,
        by_satellite=by_satellite,
        top_states=top_states,
        by_day=days_sorted,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
