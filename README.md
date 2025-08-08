# Netflix Titles Search 🎬

Una aplicación Python avanzada para búsqueda, análisis y recomendaciones de títulos de Netflix con integración de **YouTube** para trailers y **IA** para análisis de contenido y recomendaciones personalizadas.

## 📋 Descripción

Esta aplicación permite buscar, analizar y obtener recomendaciones de títulos de Netflix de manera inteligente. Incluye:

- 🔍 **Búsqueda avanzada** con múltiples criterios
- 🎥 **Integración con YouTube** para trailers automáticos
- 🤖 **Análisis de IA** para sentimiento y clasificación de contenido
- 📊 **Recomendaciones personalizadas** basadas en preferencias del usuario
- 📈 **Estadísticas detalladas** del dataset
- 🎯 **Filtros inteligentes** por género, año, rating y más

## 🏗️ Estructura del Proyecto

```
project_talent2/
├── app/
│   ├── __init__.py                 # Paquete principal
│   ├── models.py                   # Modelos Pydantic (actualizados)
│   ├── services.py                 # Lógica de búsqueda con IA
│   ├── config.py                   # Configuración global
│   ├── data_loader.py              # Carga de datos CSV
│   ├── constants.py                # Constantes y diccionarios
│   ├── youtube_service.py          # 🆕 Integración con YouTube
│   └── ai_service.py               # 🆕 Servicios de IA
├── data/
│   └── netflix_titles.csv          # Dataset de Netflix
├── main.py                         # Punto de entrada
├── requirements.txt                # Dependencias actualizadas
└── README.md                      # Este archivo
```

## 🚀 Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone <url-del-repositorio>
   cd project_talent2
   ```

2. **Crear entorno virtual:**
   ```bash
   python -m venv venv
   ```

3. **Activar entorno virtual:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

## 📊 Dataset

El proyecto utiliza el dataset `netflix_titles.csv` que contiene información sobre títulos de Netflix, incluyendo:

- **show_id**: Identificador único del título
- **type**: Tipo de contenido (Movie/TV Show)
- **title**: Título del contenido
- **director**: Director(es)
- **cast**: Reparto
- **country**: País de origen
- **date_added**: Fecha de agregado a Netflix
- **release_year**: Año de lanzamiento
- **rating**: Clasificación por edad
- **duration**: Duración
- **listed_in**: Géneros
- **description**: Descripción

## 🔧 Uso

### Ejemplo básico de uso:

```python
from app.data_loader import DataLoader
from app.services import NetflixSearchService
from app.models import SearchRequest, UserPreferences, RecommendationRequest

# Cargar datos
loader = DataLoader()
df = loader.load_data()

# Crear servicio de búsqueda con IA y YouTube
search_service = NetflixSearchService(df)

# Búsqueda con trailers y análisis de IA
request = SearchRequest(
    query="comedy",
    search_type="all",
    limit=10,
    include_trailers=True,
    include_analysis=True
)

results = search_service.search_titles(request)
print(f"Encontrados {results.total_count} resultados")

# Obtener recomendaciones personalizadas
preferences = UserPreferences(
    preferred_genres=["Dramas", "Thrillers"],
    preferred_years=[2020, 2024],
    preferred_rating=["TV-MA", "R"],
    include_trailers=True,
    include_analysis=True
)

rec_request = RecommendationRequest(
    preferences=preferences,
    limit=5
)

recommendations = search_service.get_recommendations(rec_request)
print(f"Recomendaciones: {recommendations.total_count}")
```

### Tipos de búsqueda disponibles:

- **all**: Búsqueda en todas las columnas
- **title**: Solo en títulos
- **director**: Solo en directores
- **cast**: Solo en reparto
- **description**: Solo en descripciones
- **country**: Solo en países
- **listed_in**: Solo en géneros

## 🛠️ Funcionalidades

### 🔍 NetflixSearchService
- Búsqueda avanzada con múltiples criterios
- Integración automática con YouTube para trailers
- Análisis de IA para sentimiento y clasificación
- Recomendaciones personalizadas basadas en preferencias
- Estadísticas detalladas del dataset

### 🎥 YouTubeService
- Búsqueda automática de trailers oficiales
- Información detallada de videos (duración, vistas, etc.)
- URLs de embed para integración web
- Búsqueda de videos relacionados y reviews

### 🤖 AIService
- **Análisis de sentimiento** del contenido
- **Clasificación automática de géneros**
- **Detección de advertencias de contenido**
- **Determinación de audiencia objetivo**
- **Recomendaciones inteligentes** basadas en preferencias

### 📊 DataLoader
- Carga y limpieza automática de datos
- Información estadística del dataset
- Filtros por tipo y año
- Muestreo de datos

### 📋 Modelos Pydantic (Actualizados)
- **NetflixTitle**: Representación básica de títulos
- **NetflixTitleWithMedia**: Títulos con trailers y análisis
- **VideoInfo**: Información de videos de YouTube
- **ContentAnalysis**: Análisis de IA del contenido
- **UserPreferences**: Preferencias del usuario
- **RecommendationRequest/Response**: Sistema de recomendaciones

## ⚙️ Configuración

### Configuración General
El archivo `app/config.py` contiene todas las configuraciones del proyecto:

- Rutas de archivos y datos
- Límites de búsqueda y validación
- Configuración de logging
- Parámetros de caché

### 🔑 Configuración de APIs

#### YouTube API
Para habilitar la funcionalidad de trailers, necesitas configurar la API de YouTube:

1. **Obtener API Key:**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Crea un proyecto o selecciona uno existente
   - Habilita la YouTube Data API v3
   - Crea credenciales (API Key)

2. **Configurar la API Key:**
   ```bash
   # Opción 1: Variable de entorno
   export YOUTUBE_API_KEY="tu_api_key_aqui"
   
   # Opción 2: Editar config.py
   CLAVE_API_YOUTUBE = "tu_api_key_aqui"
   ```

#### Configuración de IA
La funcionalidad de IA está habilitada por defecto y no requiere configuración adicional:
- Análisis de sentimiento
- Clasificación de géneros
- Recomendaciones personalizadas

## 📈 Estadísticas y Análisis

### Estadísticas Básicas
- Total de títulos y distribución por tipo
- Países representados y rango de años
- Información de memoria y rendimiento

### 🎯 Análisis de IA
- **Puntuación de sentimiento** (0-1)
- **Géneros predichos** automáticamente
- **Audiencia objetivo** basada en rating
- **Advertencias de contenido** detectadas
- **Puntuación de recomendación** personalizada

### 🎥 Información de YouTube
- **Trailers oficiales** automáticos
- **Estadísticas de videos** (vistas, duración)
- **Thumbnails** de alta calidad
- **URLs de embed** para integración web

### 📊 Recomendaciones Inteligentes
- **Algoritmo personalizado** basado en preferencias
- **Filtros por género, año y rating**
- **Razones de recomendación** explicadas
- **Scores de relevancia** (0-100%)

## 🧪 Testing

Para ejecutar las pruebas:

```bash
pytest tests/
```

## 📝 Desarrollo

### Estructura de código:

- **models.py**: Definición de modelos de datos
- **services.py**: Lógica de negocio
- **data_loader.py**: Manejo de datos
- **config.py**: Configuración global
- **constants.py**: Constantes y diccionarios

### Convenciones:

- Uso de type hints
- Documentación con docstrings
- Validación con Pydantic
- Logging estructurado

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Contacto

- **Autor**: [Tu Nombre]
- **Email**: [tu-email@ejemplo.com]
- **Proyecto**: [https://github.com/usuario/project_talent2](https://github.com/usuario/project_talent2)

## 🙏 Agradecimientos

- Dataset de Netflix para proporcionar los datos
- Comunidad de Python por las herramientas utilizadas
- Contribuidores del proyecto
