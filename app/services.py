import pandas as pd
from typing import List, Dict, Any, Optional
from .models import (
    NetflixTitle, SearchRequest, SearchResponse, NetflixTitleWithMedia,
    VideoInfo, ContentAnalysis, UserPreferences, RecommendationRequest,
    RecommendationResponse
)
from .constants import COLUMNAS_BUSQUEDA
from .config import CSV_FILE_PATH, CSV_ENCODING, CSV_SEPARATOR
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

        # Intento de reescritura inteligente de consulta con IA (si está activado vía flag extendido)
        # Compatibilidad: si el request trae un atributo opcional 'smart_query', úsalo
        if hasattr(request, 'smart_query') and getattr(request, 'smart_query'):
            try:
                results = self._smart_refine_results(request.query, results)
            except Exception:
                pass
        
        # Limitar resultados
        results = results[:request.limit]
        
        # Convertir a modelos Pydantic con información multimedia
        netflix_titles_with_media = []
        new_urls_added = False
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
            
            # Obtener trailer: si el dataset ya tiene 'trailer_url', úsalo; si no y se solicita, búscalo
            trailer = None
            existing_trailer_url = None
            if 'trailer_url' in self.df.columns:
                existing_trailer_url = str(row.get('trailer_url', '')).strip()
                if existing_trailer_url and existing_trailer_url.lower() != 'nan':
                    # Extraer video_id si es una URL válida de YouTube
                    video_id = None
                    if 'watch?v=' in existing_trailer_url:
                        video_id = existing_trailer_url.split('watch?v=')[-1].split('&')[0]
                    elif 'youtu.be/' in existing_trailer_url:
                        video_id = existing_trailer_url.split('youtu.be/')[-1].split('?')[0]
                    elif 'embed/' in existing_trailer_url:
                        video_id = existing_trailer_url.split('embed/')[-1].split('?')[0]
                    if video_id:
                        # Si hay API key, obtener detalles; si no, crear un objeto mínimo
                        if self.youtube_service.api_key and self.youtube_service.api_key != "TU_API_KEY_AQUI":
                            trailer = self.youtube_service._get_video_details(video_id)
                        else:
                            trailer = VideoInfo(
                                video_id=video_id,
                                title=f"{title.title} Trailer",
                                description="",
                                thumbnail_url="",
                                duration="",
                                view_count=0,
                                published_at="",
                                channel_title=""
                            )
            
            if trailer is None and request.include_trailers:
                trailer = self.youtube_service.search_trailer(
                    title.title, title.release_year
                )
                # Si se encontró y no existía en dataset, persistir URL
                if trailer and not existing_trailer_url:
                    try:
                        trailer_url = self.youtube_service.get_trailer_url(trailer.video_id)
                        self.df.at[results.index[i], 'trailer_url'] = trailer_url
                        new_urls_added = True
                    except Exception:
                        pass
            
            # Obtener análisis de IA si se solicita
            analysis = None
            if request.include_analysis:
                analysis = self.ai_service.analyze_content(title)
                # Persistir análisis LLM si llegó con crítica/sentimiento/score
                try:
                    if analysis and hasattr(analysis, 'critique') and 'critique_llm' in self.df.columns:
                        self.df.at[results.index[i], 'critique_llm'] = analysis.critique or ''
                    if analysis and 'sentiment_llm' in self.df.columns:
                        self.df.at[results.index[i], 'sentiment_llm'] = float(analysis.sentiment_score)
                    if analysis and 'score_llm' in self.df.columns:
                        self.df.at[results.index[i], 'score_llm'] = float(analysis.recommendation_score)
                    # Si ya existe una crítica guardada y el análisis no la trae, usar la guardada
                    if analysis and hasattr(analysis, 'critique') and 'critique_llm' in self.df.columns:
                        saved_crit = str(row.get('critique_llm', '')).strip()
                        if saved_crit and not analysis.critique:
                            analysis.critique = saved_crit
                except Exception:
                    pass
            
            # Crear objeto con multimedia
            title_with_media = NetflixTitleWithMedia(
                title=title,
                trailer=trailer,
                analysis=analysis
            )
            
            netflix_titles_with_media.append(title_with_media)
        
        # Persistir CSV si agregamos nuevas URLs o análisis
        if new_urls_added:
            try:
                self.df.to_csv(CSV_FILE_PATH, index=False, encoding=CSV_ENCODING, sep=CSV_SEPARATOR)
            except Exception:
                pass

        return SearchResponse(
            results=netflix_titles_with_media,
            total_count=len(netflix_titles_with_media),
            query=request.query,
            search_type=search_type
        )

    def _smart_refine_results(self, original_query: str, df: pd.DataFrame) -> pd.DataFrame:
        """Reescribe/normaliza la consulta (ES->EN, corrige typos) y filtra el DataFrame."""
        # Heurístico simple si no hay Groq: usar original
        from .ai_service import AIService
        try:
            ai = self.ai_service  # ya existe
            if not getattr(ai, 'groq_client', None):
                return df

            prompt = (
                "Usuario escribe en español una consulta de películas/series con posibles errores. "
                "Devuelve SOLO JSON con: normalized_query_en, keywords_en (lista), inferred_filters {genres, countries, type, year_range}, "
                "corrected_entities {titles, actors, directors}, notes_es (breve)."
                f"\nConsulta: {original_query}"
            )
            completion = ai.groq_client.chat.completions.create(
                model=os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'),
                messages=[
                    {"role": "system", "content": "Eres un asistente que devuelve JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=256,
            )
            import json
            data = json.loads(completion.choices[0].message.content)

            norm = str(data.get('normalized_query_en', '')).lower().strip()
            keywords = [k.lower() for k in data.get('keywords_en', [])]
            filters = data.get('inferred_filters', {}) or {}
            titles = set(map(str.lower, data.get('corrected_entities', {}).get('titles', [])))
            actors = set(map(str.lower, data.get('corrected_entities', {}).get('actors', [])))
            directors = set(map(str.lower, data.get('corrected_entities', {}).get('directors', [])))

            mask = pd.Series([True] * len(df))
            if norm:
                mask &= (
                    df['title_lower'].str.contains(norm, na=False) |
                    df['description_lower'].str.contains(norm, na=False) |
                    df['listed_in_lower'].str.contains(norm, na=False)
                )
            for kw in keywords:
                mask &= (
                    df['title_lower'].str.contains(kw, na=False) |
                    df['description_lower'].str.contains(kw, na=False) |
                    df['listed_in_lower'].str.contains(kw, na=False)
                )
            if titles:
                mask &= df['title_lower'].isin(titles) | df['title_lower'].apply(lambda t: any(tt in t for tt in titles))
            if actors and 'cast_lower' in df.columns:
                mask &= df['cast_lower'].apply(lambda c: any(a in c for a in actors))
            if directors and 'director_lower' in df.columns:
                mask &= df['director_lower'].apply(lambda d: any(di in d for di in directors))

            # Filtros extra
            yr = filters.get('year_range') or []
            if len(yr) == 2 and 'release_year' in df.columns:
                mask &= (df['release_year'] >= yr[0]) & (df['release_year'] <= yr[1])
            tp = (filters.get('type') or '').strip()
            if tp and 'type' in df.columns:
                mask &= df['type'].str.lower() == tp.lower()

            return df[mask]
        except Exception:
            return df
    
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
        new_urls_added = False
        for rec in ai_recommendations:
            # Encontrar el título correspondiente
            matching_title = next(
                (t for t in available_titles if t.title == rec.title), None
            )
            
            if matching_title:
                # Obtener trailer priorizando dataset 'trailer_url'
                trailer = None
                existing_trailer_url = None
                if 'trailer_url' in self.df.columns:
                    # Buscar la fila por show_id o por coincidencia exacta de título
                    row_idx = self.df.index[self.df['title'] == matching_title.title]
                    if len(row_idx) > 0:
                        existing_trailer_url = str(self.df.at[row_idx[0], 'trailer_url']).strip()
                
                if existing_trailer_url and existing_trailer_url.lower() != 'nan':
                    video_id = None
                    if 'watch?v=' in existing_trailer_url:
                        video_id = existing_trailer_url.split('watch?v=')[-1].split('&')[0]
                    elif 'youtu.be/' in existing_trailer_url:
                        video_id = existing_trailer_url.split('youtu.be/')[-1].split('?')[0]
                    elif 'embed/' in existing_trailer_url:
                        video_id = existing_trailer_url.split('embed/')[-1].split('?')[0]
                    if video_id:
                        if self.youtube_service.api_key and self.youtube_service.api_key != "TU_API_KEY_AQUI":
                            trailer = self.youtube_service._get_video_details(video_id)
                        else:
                            trailer = VideoInfo(
                                video_id=video_id,
                                title=f"{matching_title.title} Trailer",
                                description="",
                                thumbnail_url="",
                                duration="",
                                view_count=0,
                                published_at="",
                                channel_title=""
                            )
                
                # Si no hay en dataset y el usuario lo pide, buscar y persistir
                if trailer is None and request.preferences.include_trailers:
                    trailer = self.youtube_service.search_trailer(
                        matching_title.title, matching_title.release_year
                    )
                    if trailer and not existing_trailer_url:
                        try:
                            trailer_url = self.youtube_service.get_trailer_url(trailer.video_id)
                            # Persistir en todas las filas que coincidan con el título
                            self.df.loc[self.df['title'] == matching_title.title, 'trailer_url'] = trailer_url
                            new_urls_added = True
                        except Exception:
                            pass
                
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
        
        # Persistir CSV si agregamos nuevas URLs
        if new_urls_added:
            try:
                self.df.to_csv(CSV_FILE_PATH, index=False, encoding=CSV_ENCODING, sep=CSV_SEPARATOR)
            except Exception:
                pass

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

    def fill_trailer_urls(self, max_to_update: int = 20) -> Dict[str, Any]:
        """Busca trailers faltantes y rellena la columna 'trailer_url' en el CSV.

        Args:
            max_to_update: máximo de filas a actualizar en esta ejecución.

        Returns:
            Resumen con totales y conteos de actualizaciones.
        """
        if 'trailer_url' not in self.df.columns:
            self.df['trailer_url'] = ''

        if not self.youtube_service.api_key or self.youtube_service.api_key == "TU_API_KEY_AQUI":
            return {
                'updated': 0,
                'skipped': 0,
                'failed': 0,
                'total_missing_before': int((self.df['trailer_url'].astype(str).str.len() == 0).sum()),
                'message': 'API key de YouTube no configurada'
            }

        mask_missing = self.df['trailer_url'].astype(str).str.strip().replace('nan', '').eq('')
        missing_indices = self.df[mask_missing].index.tolist()

        updated = 0
        failed = 0
        for idx in missing_indices[:max_to_update]:
            try:
                row = self.df.loc[idx]
                title = str(row.get('title', '')).strip()
                year = row.get('release_year', None)
                year_val = int(year) if pd.notna(year) else None

                if not title:
                    continue

                video = self.youtube_service.search_trailer(title, year_val)
                if video:
                    trailer_url = self.youtube_service.get_trailer_url(video.video_id)
                    self.df.at[idx, 'trailer_url'] = trailer_url
                    updated += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        # Guardar CSV si hubo cambios
        if updated > 0:
            try:
                self.df.to_csv(CSV_FILE_PATH, index=False, encoding=CSV_ENCODING, sep=CSV_SEPARATOR)
            except Exception:
                pass

        total_missing_after = int((self.df['trailer_url'].astype(str).str.len() == 0).sum())
        return {
            'updated': updated,
            'skipped': max(0, len(missing_indices) - min(len(missing_indices), max_to_update)),
            'failed': failed,
            'total_missing_before': len(missing_indices),
            'total_missing_after': total_missing_after
        }

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
