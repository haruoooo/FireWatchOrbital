"""
Classificação de alertas de queimada por FRP (Fire Radiative Power).
"""


def classify_alert(frp: float) -> str:
    """
    Classifica o nível de alerta de um foco de queimada baseado no FRP.
    
    Args:
        frp: Radiative Power em MW
        
    Returns:
        Nível de alerta: "critical" (>=300), "high" (>=100), "medium" (>=30) ou "low"
    """
    if frp >= 300:
        return "critical"
    if frp >= 100:
        return "high"
    if frp >= 30:
        return "medium"
    return "low"
