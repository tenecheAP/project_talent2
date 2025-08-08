import requests
import logging
from typing import List, Dict, Any, Optional
from .config import CLAVE_API_YOUTUBE
from .constants import MENSAJES_ERROR
from .models import VideoInfo

# Configurar logging
logger = logging.getLogger(__name__)

class YouTubeService:
    """Servicio para interactuar con la API de YouTube"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or CLAVE_API_YOUTUBE
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        if not self.api_key or self.api_key == "TU_API_KEY_AQUI":
            logger.warning("API key de YouTube no configurada. Algunas funcionalidades no estarán disponibles.")
    
    def search_trailer(self, title: str, year: Optional[int] = None) -> Optional[VideoInfo]:
        """
        Busca el trailer oficial de una película o serie
        
        Args:
            title: Título de la película/serie
            year: Año de lanzamiento (opcional)
        
        Returns:
            VideoInfo con la información del trailer o None si no se encuentra
        """
        if not self.api_key or self.api_key == "TU_API_KEY_AQUI":
            logger.error("API key de YouTube no configurada")
            return None
        
        try:
            # Construir query de búsqueda
            query = f"{title} official trailer"
            if year:
                query += f" {year}"
            
            # Parámetros de búsqueda
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'videoCategoryId': '1',  # Film & Animation
                'maxResults': 5,
                'order': 'relevance',
                'key': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('items'):
                logger.info(f"No se encontraron trailers para: {title}")
                return None
            
            # Obtener información detallada del primer resultado
            video_id = data['items'][0]['id']['videoId']
            return self._get_video_details(video_id)
            
        except requests.RequestException as e:
            logger.error(f"Error al buscar trailer para {title}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al buscar trailer: {str(e)}")
            return None
    
    def search_related_videos(self, title: str, max_results: int = 10) -> List[VideoInfo]:
        """
        Busca videos relacionados con un título
        
        Args:
            title: Título de la película/serie
            max_results: Número máximo de resultados
        
        Returns:
            Lista de VideoInfo con videos relacionados
        """
        if not self.api_key or self.api_key == "TU_API_KEY_AQUI":
            logger.error("API key de YouTube no configurada")
            return []
        
        try:
            params = {
                'part': 'snippet',
                'q': f"{title} review analysis",
                'type': 'video',
                'maxResults': max_results,
                'order': 'relevance',
                'key': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                video_info = self._get_video_details(video_id)
                if video_info:
                    videos.append(video_info)
            
            return videos
            
        except requests.RequestException as e:
            logger.error(f"Error al buscar videos relacionados para {title}: {str(e)}")
            return []
    
    def _get_video_details(self, video_id: str) -> Optional[VideoInfo]:
        """
        Obtiene información detallada de un video
        
        Args:
            video_id: ID del video de YouTube
        
        Returns:
            VideoInfo con la información del video
        """
        try:
            params = {
                'part': 'snippet,statistics,contentDetails',
                'id': video_id,
                'key': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/videos", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('items'):
                return None
            
            item = data['items'][0]
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})
            
            return VideoInfo(
                video_id=video_id,
                title=snippet['title'],
                description=snippet['description'],
                thumbnail_url=snippet['thumbnails']['high']['url'],
                duration=content_details.get('duration', ''),
                view_count=int(statistics.get('viewCount', 0)),
                published_at=snippet['publishedAt'],
                channel_title=snippet['channelTitle']
            )
            
        except requests.RequestException as e:
            logger.error(f"Error al obtener detalles del video {video_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al obtener detalles del video: {str(e)}")
            return None
    
    def get_trailer_url(self, video_id: str) -> str:
        """
        Genera la URL del trailer
        
        Args:
            video_id: ID del video de YouTube
        
        Returns:
            URL del video
        """
        return f"https://www.youtube.com/watch?v={video_id}"
    
    def get_embed_url(self, video_id: str) -> str:
        """
        Genera la URL de embed del video
        
        Args:
            video_id: ID del video de YouTube
        
        Returns:
            URL de embed del video
        """
        return f"https://www.youtube.com/embed/{video_id}"
    
    def get_embed_html(self, video_id: str, width: int = 560, height: int = 315) -> str:
        """
        Genera el HTML del iframe para embed
        
        Args:
            video_id: ID del video de YouTube
            width: Ancho del iframe
            height: Alto del iframe
        
        Returns:
            HTML del iframe
        """
        return f'<iframe width="{width}" height="{height}" src="https://www.youtube.com/embed/{video_id}?si=5DQfQXm4_CD13NpV" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>' 