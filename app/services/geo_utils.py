"""
Utilitários geográficos: inferência de estado e bioma.
"""
from app.constants import STATE_BOXES, STATE_BIOME


def infer_state(lat: float, lon: float) -> str:
    """
    Infere o estado brasileiro pela coordenada usando bounding boxes.
    
    Args:
        lat: Latitude (-90 a 90)
        lon: Longitude (-180 a 180)
        
    Returns:
        Sigla do estado brasileiro ou "N/A"
    """
    for state, (min_lat, max_lat, min_lon, max_lon) in STATE_BOXES.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return state
    return "N/A"


def infer_biome(state: str) -> str:
    """
    Retorna o bioma dominante de um estado.
    
    Args:
        state: Sigla do estado
        
    Returns:
        Nome do bioma ou "N/A"
    """
    return STATE_BIOME.get(state, "N/A")
