import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from .models import NetflixTitle, ContentAnalysis
from .constants import GENEROS_POPULARES, CLASIFICACIONES_EDAD
from .config import GROQ_API_KEY, GROQ_MODEL

try:
    from groq import Groq
except Exception:
    Groq = None

# Configurar logging
logger = logging.getLogger(__name__)

class Recommendation:
    """Recomendación de contenido"""
    def __init__(self, title: str, score: float, reason: str, genre_match: List[str]):
        self.title = title
        self.score = score
        self.reason = reason
        self.genre_match = genre_match

class AIService:
    """Servicio de IA para análisis y recomendaciones de contenido"""
    
    def __init__(self):
        self.genre_keywords = self._load_genre_keywords()
        self.sentiment_keywords = self._load_sentiment_keywords()
        self.content_warnings = self._load_content_warnings()
        # Cliente Groq opcional
        self.groq_client = None
        if GROQ_API_KEY and Groq is not None:
            try:
                self.groq_client = Groq(api_key=GROQ_API_KEY)
            except Exception:
                self.groq_client = None
    
    def _load_genre_keywords(self) -> Dict[str, List[str]]:
        """Carga palabras clave para clasificación de géneros"""
        return {
            'Dramas': ['drama', 'emotional', 'serious', 'tragic', 'intense'],
            'Comedies': ['comedy', 'funny', 'humor', 'laugh', 'hilarious'],
            'Action & Adventure': ['action', 'adventure', 'thrilling', 'exciting', 'explosive'],
            'Thrillers': ['thriller', 'suspense', 'mystery', 'tension', 'suspenseful'],
            'Horror Movies': ['horror', 'scary', 'frightening', 'terrifying', 'spooky'],
            'Romantic TV Shows': ['romance', 'romantic', 'love', 'relationship', 'dating'],
            'Documentaries': ['documentary', 'real', 'factual', 'educational', 'informative'],
            'Children & Family Movies': ['family', 'children', 'kid', 'friendly', 'wholesome'],
            'Anime Features': ['anime', 'japanese', 'animation', 'manga', 'cartoon']
        }
    
    def _load_sentiment_keywords(self) -> Dict[str, List[str]]:
        """Carga palabras clave para análisis de sentimiento"""
        return {
            'positive': ['amazing', 'brilliant', 'excellent', 'fantastic', 'great', 'wonderful'],
            'negative': ['terrible', 'awful', 'horrible', 'bad', 'disappointing', 'boring'],
            'neutral': ['average', 'okay', 'decent', 'standard', 'normal']
        }
    
    def _load_content_warnings(self) -> Dict[str, List[str]]:
        """Carga palabras clave para advertencias de contenido"""
        return {
            'violence': ['violence', 'blood', 'gore', 'fighting', 'war'],
            'language': ['profanity', 'swearing', 'cursing', 'explicit'],
            'sexual_content': ['sexual', 'nudity', 'adult', 'mature'],
            'drugs': ['drugs', 'alcohol', 'smoking', 'substance']
        }
    
    def analyze_content(self, title: NetflixTitle) -> ContentAnalysis:
        """
        Analiza el contenido de un título usando técnicas de IA
        
        Args:
            title: Título de Netflix a analizar
        
        Returns:
            ContentAnalysis con el análisis del contenido
        """
        try:
            # Si hay Groq disponible, intentar análisis LLM primero
            if self.groq_client:
                groq_result = self._analyze_with_groq(title)
                if groq_result is not None:
                    return groq_result
            # Combinar texto para análisis
            text_for_analysis = f"{title.title} {title.description or ''} {title.listed_in or ''}"
            text_lower = text_for_analysis.lower()
            
            # Análisis de sentimiento
            sentiment_score = self._analyze_sentiment(text_lower)
            
            # Predicción de géneros
            genre_prediction = self._predict_genres(text_lower)
            
            # Audiencia objetivo
            target_audience = self._determine_target_audience(title.rating, text_lower)
            
            # Advertencias de contenido
            content_warnings = self._detect_content_warnings(text_lower)
            
            # Puntuación de recomendación
            recommendation_score = self._calculate_recommendation_score(
                sentiment_score, genre_prediction, title
            )
            
            # Títulos similares (simulado)
            similar_titles = self._find_similar_titles(title)
            
            return ContentAnalysis(
                sentiment_score=sentiment_score,
                genre_prediction=genre_prediction,
                target_audience=target_audience,
                content_warnings=content_warnings,
                recommendation_score=recommendation_score,
                similar_titles=similar_titles
            )
            
        except Exception as e:
            logger.error(f"Error al analizar contenido: {str(e)}")
            return ContentAnalysis(
                sentiment_score=0.0,
                genre_prediction=[],
                target_audience="General",
                content_warnings=[],
                recommendation_score=0.0,
                similar_titles=[]
            )

    def _analyze_with_groq(self, title: NetflixTitle) -> Optional[ContentAnalysis]:
        """Analiza usando Groq LLM y devuelve ContentAnalysis si es posible."""
        try:
            if not self.groq_client:
                return None

            prompt = (
                "Analiza este título y devuelve JSON con: sentiment (0..1), genres (lista corta), "
                "audience (texto), warnings (lista de claves), recommendation (0..1), critique_es (frase corta). "
                "Escribe en español.\n\n"
                f"Título: {title.title}\n"
                f"Descripción: {title.description or ''}\n"
                f"Géneros (dataset): {title.listed_in or ''}\n"
                f"Año: {title.release_year or ''}\n"
                f"Rating: {title.rating or ''}\n"
                "Responde SOLO JSON con estas claves: {sentiment, genres, audience, warnings, recommendation, critique_es}."
            )

            completion = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "Eres un asistente que devuelve JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=256,
            )
            content = completion.choices[0].message.content
            import json
            data = json.loads(content)

            sentiment = float(max(0.0, min(1.0, data.get("sentiment", 0.5))))
            genres = [str(g) for g in data.get("genres", [])][:3]
            audience = str(data.get("audience", "General"))
            warnings = [str(w) for w in data.get("warnings", [])]
            recommendation = float(max(0.0, min(1.0, data.get("recommendation", sentiment))))
            critique = str(data.get("critique_es", ""))

            return ContentAnalysis(
                sentiment_score=sentiment,
                genre_prediction=genres,
                target_audience=audience,
                content_warnings=warnings,
                recommendation_score=recommendation,
                similar_titles=[],
                critique=critique
            )
        except Exception:
            return None
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analiza el sentimiento del texto"""
        positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word in text)
        negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word in text)
        neutral_count = sum(1 for word in self.sentiment_keywords['neutral'] if word in text)
        
        total_keywords = positive_count + negative_count + neutral_count
        
        if total_keywords == 0:
            return 0.5  # Neutral por defecto
        
        # Calcular score entre 0 y 1
        score = (positive_count - negative_count) / total_keywords
        return max(0.0, min(1.0, (score + 1) / 2))
    
    def _predict_genres(self, text: str) -> List[str]:
        """Predice géneros basado en el texto"""
        genre_scores = {}
        
        for genre, keywords in self.genre_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                genre_scores[genre] = score
        
        # Ordenar por score y devolver los top 3
        sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
        return [genre for genre, score in sorted_genres[:3]]
    
    def _determine_target_audience(self, rating: Optional[str], text: str) -> str:
        """Determina la audiencia objetivo"""
        if not rating:
            return "General"
        
        rating_mapping = {
            'TV-Y': 'Niños pequeños',
            'TV-Y7': 'Niños 7+',
            'TV-G': 'Audiencia general',
            'TV-PG': 'Niños con supervisión parental',
            'TV-14': 'Adolescentes 14+',
            'TV-MA': 'Adultos',
            'G': 'Audiencia general',
            'PG': 'Niños con supervisión parental',
            'PG-13': 'Adolescentes 13+',
            'R': 'Adultos',
            'NC-17': 'Solo adultos'
        }
        
        return rating_mapping.get(rating, "General")
    
    def _detect_content_warnings(self, text: str) -> List[str]:
        """Detecta advertencias de contenido"""
        warnings = []
        
        for warning_type, keywords in self.content_warnings.items():
            if any(keyword in text for keyword in keywords):
                warnings.append(warning_type)
        
        return warnings
    
    def _calculate_recommendation_score(self, sentiment: float, genres: List[str], title: NetflixTitle) -> float:
        """Calcula una puntuación de recomendación"""
        base_score = sentiment * 0.4  # 40% sentimiento
        
        # Bonus por géneros populares
        genre_bonus = sum(0.1 for genre in genres if genre in GENEROS_POPULARES)
        
        # Bonus por año reciente
        year_bonus = 0.0
        if title.release_year:
            current_year = 2024
            if title.release_year >= current_year - 5:
                year_bonus = 0.2
            elif title.release_year >= current_year - 10:
                year_bonus = 0.1
        
        return min(1.0, base_score + genre_bonus + year_bonus)
    
    def _find_similar_titles(self, title: NetflixTitle) -> List[str]:
        """Encuentra títulos similares (simulado)"""
        # Simulación de títulos similares basado en género
        similar_titles = []
        
        if title.listed_in:
            if 'Drama' in title.listed_in:
                similar_titles.extend(['Breaking Bad', 'The Crown', 'Ozark'])
            if 'Comedy' in title.listed_in:
                similar_titles.extend(['The Office', 'Friends', 'Parks and Recreation'])
            if 'Action' in title.listed_in:
                similar_titles.extend(['The Witcher', 'Stranger Things', 'Money Heist'])
        
        return similar_titles[:3]
    
    def get_recommendations(self, user_preferences: Dict[str, Any], available_titles: List[NetflixTitle]) -> List[Recommendation]:
        """
        Genera recomendaciones personalizadas
        
        Args:
            user_preferences: Preferencias del usuario
            available_titles: Lista de títulos disponibles
        
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        for title in available_titles:
            analysis = self.analyze_content(title)
            
            # Calcular score de recomendación personalizada
            score = self._calculate_personalized_score(title, analysis, user_preferences)
            
            if score > 0.3:  # Solo recomendar si score > 30%
                reason = self._generate_recommendation_reason(title, analysis, user_preferences)
                
                recommendations.append(Recommendation(
                    title=title.title,
                    score=score,
                    reason=reason,
                    genre_match=analysis.genre_prediction
                ))
        
        # Ordenar por score y devolver top 10
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:10]
    
    def _calculate_personalized_score(self, title: NetflixTitle, analysis: ContentAnalysis, preferences: Dict[str, Any]) -> float:
        """Calcula score personalizado basado en preferencias"""
        score = analysis.recommendation_score
        
        # Ajustar por preferencias de género
        if 'preferred_genres' in preferences:
            genre_match = any(genre in preferences['preferred_genres'] for genre in analysis.genre_prediction)
            if genre_match:
                score += 0.3
        
        # Ajustar por rango de años preferido
        if 'preferred_years' in preferences and title.release_year:
            year_range = preferences['preferred_years']
            if year_range[0] <= title.release_year <= year_range[1]:
                score += 0.2
        
        # Ajustar por rating preferido
        if 'preferred_rating' in preferences and title.rating:
            if title.rating in preferences['preferred_rating']:
                score += 0.1
        
        return min(1.0, score)
    
    def _generate_recommendation_reason(self, title: NetflixTitle, analysis: ContentAnalysis, preferences: Dict[str, Any]) -> str:
        """Genera una razón para la recomendación"""
        reasons = []
        
        if analysis.sentiment_score > 0.7:
            reasons.append("Muy bien valorado")
        elif analysis.sentiment_score > 0.5:
            reasons.append("Bien valorado")
        
        if analysis.genre_prediction:
            reasons.append(f"Género: {', '.join(analysis.genre_prediction)}")
        
        if title.release_year and title.release_year >= 2020:
            reasons.append("Contenido reciente")
        
        if not reasons:
            reasons.append("Basado en tus preferencias")
        
        return ". ".join(reasons) 