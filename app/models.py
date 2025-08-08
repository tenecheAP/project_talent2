from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class NetflixTitle(BaseModel):
    """Modelo para representar un título de Netflix"""
    show_id: str
    type: str
    title: str
    director: Optional[str] = None
    cast: Optional[str] = None
    country: Optional[str] = None
    date_added: Optional[str] = None
    release_year: Optional[int] = None
    rating: Optional[str] = None
    duration: Optional[str] = None
    listed_in: Optional[str] = None
    description: Optional[str] = None

class VideoInfo(BaseModel):
    """Información de video de YouTube"""
    video_id: str
    title: str
    description: str
    thumbnail_url: str
    duration: str
    view_count: int
    published_at: str
    channel_title: str

class ContentAnalysis(BaseModel):
    """Análisis de contenido por IA"""
    sentiment_score: float
    genre_prediction: List[str]
    target_audience: str
    content_warnings: List[str]
    recommendation_score: float
    similar_titles: List[str]

class NetflixTitleWithMedia(BaseModel):
    """Título de Netflix con información multimedia"""
    title: NetflixTitle
    trailer: Optional[VideoInfo] = None
    analysis: Optional[ContentAnalysis] = None

class SearchRequest(BaseModel):
    """Modelo para las solicitudes de búsqueda"""
    query: str
    search_type: str = "all"  # all, title, director, cast, description
    limit: int = 10
    include_trailers: bool = False
    include_analysis: bool = False

class SearchResponse(BaseModel):
    """Modelo para las respuestas de búsqueda"""
    results: List[NetflixTitleWithMedia]
    total_count: int
    query: str
    search_type: str

class UserPreferences(BaseModel):
    """Preferencias del usuario para recomendaciones"""
    preferred_genres: List[str] = []
    preferred_years: List[int] = []
    preferred_rating: List[str] = []
    max_duration: Optional[int] = None
    include_trailers: bool = True
    include_analysis: bool = True

class RecommendationRequest(BaseModel):
    """Solicitud de recomendaciones"""
    preferences: UserPreferences
    limit: int = 10

class RecommendationResponse(BaseModel):
    """Respuesta de recomendaciones"""
    recommendations: List[NetflixTitleWithMedia]
    total_count: int
    user_preferences: UserPreferences

# Modelo legacy para compatibilidad
class Pelicula(BaseModel):
    title: str
    director: str
    cast: str
    country: str
    release_year: int
    listed_in: str
    type: str
