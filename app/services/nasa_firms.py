"""
Integração com NASA FIRMS API e geração de dados sintéticos.
"""
import csv
import io
import random
import logging
from datetime import datetime, timedelta
import httpx

from app.models import FireData
from app.constants import BIOMES, STATES, BRAZIL_BOUNDS
from app.services.geo_utils import infer_state, infer_biome

logger = logging.getLogger("firewatch")


def _normalize_confidence(value: str | None) -> str:
    """Normaliza confidence da NASA (n/h/l) para low/nominal/high."""
    if not value:
        return "nominal"
    val = str(value).strip().lower()
    mapping = {
        "h": "high",
        "high": "high",
        "n": "nominal",
        "nominal": "nominal",
        "l": "low",
        "low": "low",
    }
    return mapping.get(val, "nominal")


async def fetch_nasa_firms(api_key: str, days: int = 5) -> list[FireData]:
    """
    Busca dados de focos de queimada da NASA FIRMS.
    
    Args:
        api_key: Chave da API NASA FIRMS
        days: Número de dias históricos (1-5)
        
    Returns:
        Lista de focos com metadados (estado, bioma, alert_level)
        
    Raises:
        ValueError: Se API_KEY não estiver configurada ou resposta inválida
    """
    if not api_key:
        raise ValueError("NASA_API_KEY não configurada")
    
    nasa_firms_base = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    
    # Bounding box do Brasil
    url = (
        f"{nasa_firms_base}/{api_key}/VIIRS_NOAA20_NRT/"
        f"{BRAZIL_BOUNDS['min_lon']},{BRAZIL_BOUNDS['min_lat']},"
        f"{BRAZIL_BOUNDS['max_lon']},{BRAZIL_BOUNDS['max_lat']}/{days}"
    )
    
    logger.info("Chamando NASA FIRMS: %s", url.replace(api_key, "***KEY***"))
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    
    text = resp.text.strip()
    logger.info("NASA FIRMS respondeu %d chars", len(text))
    
    if not text or text.lower().startswith("invalid") or "error" in text.lower()[:100]:
        raise ValueError(f"NASA FIRMS retornou erro: {text[:200]}")
    
    reader = csv.DictReader(io.StringIO(text))
    
    if reader.fieldnames is None or "latitude" not in (reader.fieldnames or []):
        raise ValueError(f"Resposta inesperada da NASA FIRMS: {text[:200]}")
    
    fires = []
    for i, row in enumerate(reader):
        try:
            lat = float(row.get("latitude", 0))
            lon = float(row.get("longitude", 0))
            state = infer_state(lat, lon)
            biome = infer_biome(state)
            
            fire = FireData(
                id=i + 1,
                latitude=lat,
                longitude=lon,
                brightness=float(row.get("bright_ti4", row.get("brightness", 0))),
                scan=float(row.get("scan", 0)),
                track=float(row.get("track", 0)),
                acq_date=row.get("acq_date", ""),
                acq_time=row.get("acq_time", ""),
                satellite=row.get("satellite", ""),
                frp=float(row.get("frp", 0)),
                confidence=_normalize_confidence(row.get("confidence")),
                biome=biome,
                state=state,
                source="nasa_firms",
            )
            fires.append(fire)
        except (ValueError, KeyError) as e:
            logger.debug(f"Erro ao processar fogo {i}: {e}")
            continue
    
    logger.info("NASA FIRMS: %d focos carregados", len(fires))
    return fires


def generate_synthetic_fires(count: int = 200) -> list[FireData]:
    """
    Gera dados de queimadas sintéticos para testes e fallback.
    
    Args:
        count: Número de focos a gerar
        
    Returns:
        Lista de focos sintéticos
    """
    random.seed(42)
    fires = []
    hotspot_regions = [
        (-10.5, -62.0, 2.5),  # Amazônia
        (-12.0, -55.0, 3.0),  # Pará
        (-8.0,  -45.0, 2.0),  # Tocantins
        (-15.0, -47.0, 1.5),  # Brasília
        (-4.0,  -52.0, 2.0),  # Amazonas
    ]
    
    for i in range(count):
        acq_date = datetime.now() - timedelta(days=random.randint(0, 7))
        lat_c, lon_c, spread = random.choice(hotspot_regions)
        lat = round(lat_c + random.uniform(-spread, spread), 4)
        lon = round(lon_c + random.uniform(-spread, spread), 4)
        state = infer_state(lat, lon)
        biome = infer_biome(state)
        
        fire = FireData(
            id=i + 1,
            latitude=lat,
            longitude=lon,
            brightness=round(random.uniform(310, 430), 1),
            scan=round(random.uniform(0.4, 2.0), 2),
            track=round(random.uniform(0.4, 2.0), 2),
            acq_date=acq_date.strftime("%Y-%m-%d"),
            acq_time=f"{random.randint(0,23):02d}{random.randint(0,59):02d}",
            satellite=random.choice(["Terra", "Aqua", "NOAA-20", "SNPP"]),
            frp=round(random.uniform(5, 800), 1),
            confidence=random.choice(["low", "nominal", "high"]),
            biome=biome,
            state=state,
            source="synthetic",
        )
        fires.append(fire)
    
    return fires
