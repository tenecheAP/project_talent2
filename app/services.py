import pandas as pd
from typing import List, Dict, Any, Optional
from .models import (
    NetflixTitle, SearchRequest, SearchResponse, NetflixTitleWithMedia,
    VideoInfo, ContentAnalysis, UserPreferences, RecommendationRequest,
    RecommendationResponse
)
from .constants import COLUMNAS_BUSQUEDA
from .youtube_service import YouTubeService
from .ai_service import AIService
import re

class NetflixSearchService:
    """Servicio para búsqueda en datos de Netflix con integración de YouTube e IA"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.youtube_service = YouTubeService()
        self.ai_service = AIService()
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepara los datos para búsqueda"""
        # Limpiar datos nulos
        for col in self.df.columns:
            self.df[col] = self.df[col].fillna('')
        
        # Convertir a minúsculas para búsqueda
        for col in COLUMNAS_BUSQUEDA:
            if col in self.df.columns:
                self.df[f'{col}_lower'] = self.df[col].str.lower()
    
    def search_titles(self, request: SearchRequest) -> SearchResponse:
        """Realiza búsqueda de títulos con integración multimedia"""
        query = request.query.lower()
        search_type = request.search_type
        
        if search_type == "all":
            results = self._search_all_columns(query)
        else:
            results = self._search_specific_column(query, search_type)
        
        # Limitar resultados
        results = results[:request.limit]
        
        # Convertir a modelos Pydantic con información multimedia
        netflix_titles_with_media = []
        for i, (_, row) in enumerate(results.iterrows()):
            # Crear NetflixTitle
            title = NetflixTitle(
                show_id=row['show_id'],
                type=row['type'],
                title=row['title'],
                director=row['director'] if pd.notna(row['director']) else None,
                cast=row['cast'] if pd.notna(row['cast']) else None,
                country=row['country'] if pd.notna(row['country']) else None,
                date_added=row['date_added'] if pd.notna(row['date_added']) else None,
                release_year=row['release_year'] if pd.notna(row['release_year']) else None,
                rating=row['rating'] if pd.notna(row['rating']) else None,
                duration=row['duration'] if pd.notna(row['duration']) else None,
                listed_in=row['listed_in'] if pd.notna(row['listed_in']) else None,
                description=row['description'] if pd.notna(row['description']) else None
            )
            
            # Obtener trailer si se solicita (solo para los primeros 3 resultados)
            trailer = None
            if request.include_trailers and i < 3:
                trailer = self.youtube_service.search_trailer(
                    title.title, title.release_year
                )
            
            # Obtener análisis de IA si se solicita
            analysis = None
            if request.include_analysis:
                analysis = self.ai_service.analyze_content(title)
            
            # Crear objeto con multimedia
            title_with_media = NetflixTitleWithMedia(
                title=title,
                trailer=trailer,
                analysis=analysis
            )
            
            netflix_titles_with_media.append(title_with_media)
        
        return SearchResponse(
            results=netflix_titles_with_media,
            total_count=len(netflix_titles_with_media),
            query=request.query,
            search_type=search_type
        )
    
    def _search_all_columns(self, query: str) -> pd.DataFrame:
        """Búsqueda en todas las columnas de búsqueda"""
        mask = pd.Series([False] * len(self.df))
        
        for col in COLUMNAS_BUSQUEDA:
            if col in self.df.columns:
                col_mask = self.df[f'{col}_lower'].str.contains(query, na=False)
                mask = mask | col_mask
        
        return self.df[mask]
    
    def _search_specific_column(self, query: str, column: str) -> pd.DataFrame:
        """Búsqueda en una columna específica"""
        if column not in self.df.columns:
            return pd.DataFrame()
        
        mask = self.df[f'{column}_lower'].str.contains(query, na=False)
        return self.df[mask]
    
    def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Genera recomendaciones personalizadas usando IA"""
        # Convertir DataFrame a lista de NetflixTitle
        available_titles = []
        for _, row in self.df.iterrows():
            title = NetflixTitle(
                show_id=row['show_id'],
                type=row['type'],
                title=row['title'],
                director=row['director'] if pd.notna(row['director']) else None,
                cast=row['cast'] if pd.notna(row['cast']) else None,
                country=row['country'] if pd.notna(row['country']) else None,
                date_added=row['date_added'] if pd.notna(row['date_added']) else None,
                release_year=row['release_year'] if pd.notna(row['release_year']) else None,
                rating=row['rating'] if pd.notna(row['rating']) else None,
                duration=row['duration'] if pd.notna(row['duration']) else None,
                listed_in=row['listed_in'] if pd.notna(row['listed_in']) else None,
                description=row['description'] if pd.notna(row['description']) else None
            )
            available_titles.append(title)
        
        # Obtener recomendaciones de IA
        ai_recommendations = self.ai_service.get_recommendations(
            request.preferences.dict(), available_titles
        )
        
        # Convertir a NetflixTitleWithMedia
        recommendations_with_media = []
        for rec in ai_recommendations:
            # Encontrar el título correspondiente
            matching_title = next(
                (t for t in available_titles if t.title == rec.title), None
            )
            
            if matching_title:
                # Obtener trailer si se solicita
                trailer = None
                if request.preferences.include_trailers:
                    trailer = self.youtube_service.search_trailer(
                        matching_title.title, matching_title.release_year
                    )
                
                # Obtener análisis si se solicita
                analysis = None
                if request.preferences.include_analysis:
                    analysis = self.ai_service.analyze_content(matching_title)
                
                title_with_media = NetflixTitleWithMedia(
                    title=matching_title,
                    trailer=trailer,
                    analysis=analysis
                )
                
                recommendations_with_media.append(title_with_media)
        
        return RecommendationResponse(
            recommendations=recommendations_with_media[:request.limit],
            total_count=len(recommendations_with_media),
            user_preferences=request.preferences
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del dataset"""
        stats = {
            'total_titles': len(self.df),
            'movies': len(self.df[self.df['type'] == 'Movie']),
            'tv_shows': len(self.df[self.df['type'] == 'TV Show']),
            'countries': self.df['country'].nunique(),
            'years_range': {
                'min': self.df['release_year'].min(),
                'max': self.df['release_year'].max()
            }
        }
        return stats

# Funciones legacy para compatibilidad
from app.models import Pelicula
from app.data_loader import cargar_datos_csv

df = cargar_datos_csv()

def buscar_peliculas(columna: str, valor: str) -> list[Pelicula]:
    resultados = df[df[columna].str.contains(valor, case=False, na=False)]
    peliculas = [
        Pelicula(
            title=str(row['title']) if pd.notnull(row['title']) else "",
            director=str(row['director']) if pd.notna(row['director']) else "",
            cast=str(row['cast']) if pd.notna(row['cast']) else "",
            country=str(row['country']) if pd.notna(row['country']) else "",
            release_year=int(row['release_year']) if pd.notna(row['release_year']) else 0,
            listed_in=str(row['listed_in']) if pd.notna(row['listed_in']) else "",
            type=str(row['type']) if pd.notna(row['type']) else ""
        )
        for _, row in resultados.head(10).iterrows()
    ]
    return peliculas
