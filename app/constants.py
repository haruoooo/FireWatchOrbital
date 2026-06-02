"""
Constantes da aplicação: estados, biomas, bounding boxes.
"""

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

# Limites geográficos do Brasil
BRAZIL_BOUNDS = {
    "min_lat": -33.75,
    "max_lat":   5.27,
    "min_lon": -73.99,
    "max_lon": -28.85,
}
