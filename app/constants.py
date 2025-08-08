# Columnas disponibles para búsqueda
COLUMNAS_BUSQUEDA = [
    'title',
    'director', 
    'cast',
    'description',
    'country',
    'listed_in'
]

# Tipos de contenido disponibles
TIPOS_CONTENIDO = [
    'Movie',
    'TV Show'
]

# Clasificaciones de edad disponibles
CLASIFICACIONES_EDAD = [
    'TV-Y',
    'TV-Y7',
    'TV-Y7-FV',
    'TV-G',
    'TV-PG',
    'TV-14',
    'TV-MA',
    'G',
    'PG',
    'PG-13',
    'R',
    'NC-17',
    'UR',
    'NR'
]

# Países más comunes en Netflix
PAISES_COMUNES = [
    'United States',
    'India',
    'United Kingdom',
    'Canada',
    'Spain',
    'France',
    'Germany',
    'Japan',
    'South Korea',
    'Brazil',
    'Mexico',
    'Australia'
]

# Géneros más populares
GENEROS_POPULARES = [
    'Dramas',
    'Comedies',
    'Documentaries',
    'Action & Adventure',
    'International TV Shows',
    'Romantic TV Shows',
    'Children & Family Movies',
    'Thrillers',
    'Horror Movies',
    'Anime Features'
]

# Configuración de búsqueda por defecto
CONFIG_BUSQUEDA_DEFAULT = {
    'limit': 10,
    'search_type': 'all',
    'case_sensitive': False
}

# Mensajes de error comunes
MENSAJES_ERROR = {
    'archivo_no_encontrado': 'El archivo de datos no fue encontrado',
    'datos_vacios': 'No se encontraron datos para procesar',
    'busqueda_vacia': 'La consulta de búsqueda no puede estar vacía',
    'tipo_busqueda_invalido': 'El tipo de búsqueda especificado no es válido',
    'limite_excedido': 'El límite de resultados excede el máximo permitido'
}

# Configuración de validación
VALIDACION = {
    'min_query_length': 2,
    'max_query_length': 100,
    'max_results': 100,
    'min_year': 1900,
    'max_year': 2030
}

# Configuración de formato de fecha
FORMATO_FECHA = '%B %d, %Y'

# Configuración de duración
FORMATO_DURACION = {
    'movie': 'min',
    'tv_show': 'Season'
}

# Configuración de caché
CACHE_CONFIG = {
    'enabled': True,
    'ttl': 300,  # 5 minutos
    'max_size': 1000
}

# Mapeo de columnas para compatibilidad con código legacy
columnas_busqueda = {
    "Título": "title",
    "Director": "director",
    "Reparto": "cast",
    "País": "country",
    "Año de lanzamiento": "release_year",
    "Género": "listed_in",
    "Tipo": "type"
}
