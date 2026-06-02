import os
import csv
import io
import random
import logging
import httpx
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("firewatch")

# Carrega .env se existir (desenvolvimento local)
_env_file = Path(__file__).resolve().parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

# Caminhos absolutos — funciona independente de onde o uvicorn é chamado
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="FireWatch Orbital API",
    description="Monitoramento de queimadas com dados orbitais da NASA FIRMS",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

NASA_FIRMS_KEY = os.getenv("NASA_API_KEY", "")
NASA_FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

BRAZIL_BOUNDS = {
    "min_lat": -33.75,
    "max_lat":   5.27,
    "min_lon": -73.99,
    "max_lon": -28.85,
}

BIOMES = ["Amazônia", "Cerrado", "Mata Atlântica", "Caatinga", "Pantanal", "Pampa"]
STATES = [
    "AM", "PA", "MT", "MS", "GO", "BA", "MG", "SP", "PR", "RS",
    "RO", "AC", "TO", "MA", "PI", "CE", "RN", "PB", "PE", "AL",
    "SE", "ES", "RJ", "SC", "AP", "RR", "DF"
]

# Bounding boxes aproximados por estado: (min_lat, max_lat, min_lon, max_lon)
STATE_BOXES = {
    "AM": (-9.8,  2.2,  -73.9, -56.1),
    "PA": (-9.8,  2.5,  -58.5, -46.0),
    "MT": (-18.0, -7.3, -61.5, -50.2),
    "MS": (-24.0, -17.0,-57.7, -50.9),
    "GO": (-19.5, -12.4,-53.2, -45.9),
    "BA": (-18.3,  -8.5, -46.6, -37.3),
    "MG": (-22.9, -14.2,-51.0, -39.8),
    "SP": (-25.3, -19.8,-53.1, -44.1),
    "PR": (-26.7, -22.5,-54.6, -48.0),
    "RS": (-33.7, -27.1,-57.6, -49.7),
    "RO": (-13.7,  -7.9, -66.8, -59.8),
    "AC": (-11.1,  -7.1, -73.9, -66.5),
    "TO": (-13.4,  -5.1, -50.7, -45.5),
    "MA": (-10.2,  -1.0, -48.2, -41.8),
    "PI": (-11.5,  -2.7, -45.9, -40.3),
    "CE": ( -7.8,  -2.8, -41.4, -37.2),
    "RN": ( -6.9,  -4.8, -38.6, -35.0),
    "PB": ( -8.3,  -6.0, -38.8, -34.8),
    "PE": ( -9.5,  -7.3, -41.4, -34.8),
    "AL": ( -10.5, -8.8, -38.2, -35.1),
    "SE": ( -11.6, -9.5, -38.2, -36.4),
    "ES": ( -21.3, -17.9,-41.9, -39.6),
    "RJ": ( -23.4, -20.8,-44.9, -40.9),
    "SC": ( -29.4, -25.9,-53.9, -48.4),
    "AP": (  0.0,   4.4, -52.0, -49.9),
    "RR": (  1.1,   5.3, -64.8, -58.9),
    "DF": (-16.1, -15.5,-48.3, -47.3),
}

# Bioma dominante por estado
STATE_BIOME = {
    "AM": "Amazônia",  "PA": "Amazônia",  "AP": "Amazônia",
    "RR": "Amazônia",  "AC": "Amazônia",  "RO": "Amazônia",
    "MT": "Cerrado",   "TO": "Cerrado",   "GO": "Cerrado",
    "DF": "Cerrado",   "MS": "Pantanal",  "MA": "Cerrado",
    "PI": "Caatinga",  "CE": "Caatinga",  "RN": "Caatinga",
    "PB": "Caatinga",  "PE": "Caatinga",  "AL": "Mata Atlântica",
    "SE": "Mata Atlântica", "BA": "Caatinga", "MG": "Cerrado",
    "ES": "Mata Atlântica", "RJ": "Mata Atlântica", "SP": "Mata Atlântica",
    "PR": "Mata Atlântica", "SC": "Mata Atlântica", "RS": "Pampa",
}


def infer_state(lat: float, lon: float) -> str:
    """Infere o estado brasileiro pela coordenada usando bounding boxes."""
    for state, (min_lat, max_lat, min_lon, max_lon) in STATE_BOXES.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return state
    return "N/A"


def infer_biome(state: str) -> str:
    """Retorna o bioma dominante de um estado."""
    return STATE_BIOME.get(state, "N/A")


def generate_synthetic_fires(count: int = 200) -> list[dict]:
    random.seed(42)
    fires = []
    hotspot_regions = [
        (-10.5, -62.0, 2.5),
        (-12.0, -55.0, 3.0),
        (-8.0,  -45.0, 2.0),
        (-15.0, -47.0, 1.5),
        (-4.0,  -52.0, 2.0),
    ]
    for i in range(count):
        acq_date = datetime.now() - timedelta(days=random.randint(0, 7))
        lat_c, lon_c, spread = random.choice(hotspot_regions)
        lat = round(lat_c + random.uniform(-spread, spread), 4)
        lon = round(lon_c + random.uniform(-spread, spread), 4)
        fires.append({
            "id": i + 1,
            "latitude": lat,
            "longitude": lon,
            "brightness": round(random.uniform(310, 430), 1),
            "scan": round(random.uniform(0.4, 2.0), 2),
            "track": round(random.uniform(0.4, 2.0), 2),
            "acq_date": acq_date.strftime("%Y-%m-%d"),
            "acq_time": f"{random.randint(0,23):02d}{random.randint(0,59):02d}",
            "satellite": random.choice(["Terra", "Aqua", "NOAA-20", "SNPP"]),
            "frp": round(random.uniform(5, 800), 1),
            "confidence": random.choice(["low", "nominal", "high"]),
            "biome": random.choice(BIOMES),
            "state": random.choice(STATES),
            "source": "synthetic",
        })
    return fires


async def fetch_nasa_firms(days: int = 5) -> list[dict]:
    if not NASA_FIRMS_KEY:
        raise ValueError("NASA_API_KEY não configurada")

    # Bounding box do Brasil
    url = (
        f"{NASA_FIRMS_BASE}/{NASA_FIRMS_KEY}/VIIRS_NOAA20_NRT/"
        f"{BRAZIL_BOUNDS['min_lon']},{BRAZIL_BOUNDS['min_lat']},"
        f"{BRAZIL_BOUNDS['max_lon']},{BRAZIL_BOUNDS['max_lat']}/{days}"
    )
    logger.info("Chamando NASA FIRMS: %s", url.replace(NASA_FIRMS_KEY, "***KEY***"))

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    text = resp.text.strip()
    logger.info("NASA FIRMS respondeu %d chars, início: %s", len(text), text[:80])

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
            fires.append({
                "id": i + 1,
                "latitude": lat,
                "longitude": lon,
                "brightness": float(row.get("bright_ti4", row.get("brightness", 0))),
                "scan": float(row.get("scan", 0)),
                "track": float(row.get("track", 0)),
                "acq_date": row.get("acq_date", ""),
                "acq_time": row.get("acq_time", ""),
                "satellite": row.get("satellite", ""),
                "frp": float(row.get("frp", 0)),
                "confidence": row.get("confidence", "nominal"),
                "biome": biome,
                "state": state,
                "source": "nasa_firms",
            })
        except (ValueError, KeyError):
            continue

    logger.info("NASA FIRMS: %d focos carregados", len(fires))
    return fires


def classify_alert(frp: float) -> str:
    if frp >= 300:
        return "critical"
    if frp >= 100:
        return "high"
    if frp >= 30:
        return "medium"
    return "low"


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=(TEMPLATES_DIR / "index.html").read_text(encoding="utf-8"))

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "nasa_key_configured": bool(NASA_FIRMS_KEY),
    }

@app.get("/api/debug")
async def debug_nasa():
    """Mostra a resposta bruta da NASA FIRMS — útil para diagnosticar problemas com a chave."""
    if not NASA_FIRMS_KEY:
        return {"error": "NASA_API_KEY não está definida no .env"}
    url = (
        f"{NASA_FIRMS_BASE}/{NASA_FIRMS_KEY}/MODIS_NRT/"
        f"{BRAZIL_BOUNDS['min_lon']},{BRAZIL_BOUNDS['min_lat']},"
        f"{BRAZIL_BOUNDS['max_lon']},{BRAZIL_BOUNDS['max_lat']}/1"
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
        return {
            "url_chamada": url.replace(NASA_FIRMS_KEY, "***KEY***"),
            "status_http": resp.status_code,
            "primeiros_500_chars": resp.text[:500],
            "key_configurada": bool(NASA_FIRMS_KEY),
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/fires")
async def get_fires(
    days: int = Query(default=5, ge=1, le=5),
    confidence: Optional[str] = Query(default=None),
    min_frp: float = Query(default=0),
):
    try:
        fires = await fetch_nasa_firms(days)
        data_source = "nasa_firms"
    except Exception as e:
        logger.warning("Fallback para dados sintéticos. Motivo: %s", e)
        fires = generate_synthetic_fires(250)
        data_source = "synthetic"

    if confidence:
        fires = [f for f in fires if f.get("confidence") == confidence]
    if min_frp > 0:
        fires = [f for f in fires if f.get("frp", 0) >= min_frp]

    for f in fires:
        f["alert_level"] = classify_alert(f["frp"])

    return {
        "total": len(fires),
        "data_source": data_source,
        "period_days": days,
        "fires": fires,
        "updated_at": datetime.utcnow().isoformat(),
    }

@app.get("/api/stats")
async def get_stats():
    try:
        fires = await fetch_nasa_firms(5)
        data_source = "nasa_firms"
    except Exception as e:
        logger.warning("Stats — fallback para dados sintéticos. Motivo: %s", e)
        fires = generate_synthetic_fires(250)
        data_source = "synthetic"

    for f in fires:
        f["alert_level"] = classify_alert(f["frp"])

    by_biome: dict[str, int] = {}
    by_state: dict[str, int] = {}
    by_alert: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_day: dict[str, int] = {}
    by_satellite: dict[str, int] = {}

    for f in fires:
        biome = f.get("biome", "N/A")
        state = f.get("state", "N/A")
        alert = f.get("alert_level", "low")
        day = f.get("acq_date", "")
        sat = f.get("satellite", "N/A")
        by_biome[biome] = by_biome.get(biome, 0) + 1
        by_state[state] = by_state.get(state, 0) + 1
        by_alert[alert] = by_alert.get(alert, 0) + 1
        by_day[day] = by_day.get(day, 0) + 1
        by_satellite[sat] = by_satellite.get(sat, 0) + 1

    top_states = sorted(by_state.items(), key=lambda x: x[1], reverse=True)[:10]
    days_sorted = sorted(by_day.items())
    frp_values = [f["frp"] for f in fires if f["frp"] > 0]
    avg_frp = round(sum(frp_values) / len(frp_values), 1) if frp_values else 0
    max_frp = round(max(frp_values), 1) if frp_values else 0

    return {
        "total_fires": len(fires),
        "data_source": data_source,
        "avg_frp": avg_frp,
        "max_frp": max_frp,
        "critical_count": by_alert["critical"],
        "high_count": by_alert["high"],
        "by_biome": by_biome,
        "by_alert": by_alert,
        "by_satellite": by_satellite,
        "top_states": dict(top_states),
        "by_day": dict(days_sorted),
        "updated_at": datetime.utcnow().isoformat(),
    }
