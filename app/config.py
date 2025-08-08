import os
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_FILE_PATH = DATA_DIR / "netflix_titles.csv"

# Configuración de la aplicación
APP_NAME = "Netflix Titles Search"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Aplicación para búsqueda y análisis de títulos de Netflix con IA y YouTube"

# Configuración de búsqueda
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 100
DEFAULT_SEARCH_TYPE = "all"

# Configuración de logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configuración de desarrollo
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Configuración de datos
CSV_ENCODING = "utf-8"
CSV_SEPARATOR = ","

# Configuración de validación
MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 100

# Tipos de búsqueda disponibles
SEARCH_TYPES = [
    "all",
    "title", 
    "director",
    "cast",
    "description",
    "country",
    "listed_in"
]

# Configuración de caché
CACHE_ENABLED = True
CACHE_TTL = 300  # 5 minutos en segundos

# Configuración de APIs
CLAVE_API_YOUTUBE = os.getenv("YOUTUBE_API_KEY", "AIzaSyDmWxGseVwbGliWZRRgPZH3npmTRZVIu6g")

# Configuración de IA
AI_ENABLED = True
SENTIMENT_ANALYSIS_ENABLED = True
RECOMMENDATION_ENGINE_ENABLED = True

# Configuración de YouTube
YOUTUBE_MAX_RESULTS = 5
YOUTUBE_CATEGORY_ID = "1"  # Film & Animation
