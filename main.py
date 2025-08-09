import streamlit as st
import pandas as pd
from app.data_loader import DataLoader
from app.services import NetflixSearchService
from app.models import SearchRequest, UserPreferences, RecommendationRequest
from app.constants import columnas_busqueda

# Utilidad para mostrar calificación con estrellas (0-5)
def render_star_rating(score: float, max_stars: int = 5) -> str:
    try:
        clamped = max(0.0, min(1.0, float(score)))
    except Exception:
        clamped = 0.0
    filled = int(round(clamped * max_stars))
    return "⭐" * filled + "☆" * (max_stars - filled)

# Configurar página
st.set_page_config(
    page_title="Netflix Titles Search",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Netflix Titles Search")
st.markdown("### Búsqueda y Análisis Inteligente de Títulos de Netflix")

# Cargar datos
@st.cache_data
def load_data():
    loader = DataLoader()
    return loader.load_data()

try:
    df = load_data()
    search_service = NetflixSearchService(df)
    st.success(f"✅ Datos cargados exitosamente: {len(df)} títulos")
except Exception as e:
    st.error(f"❌ Error al cargar datos: {str(e)}")
    st.stop()

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Opciones de búsqueda
    include_trailers = st.checkbox("🎥 Incluir trailers de YouTube", value=False)
    include_analysis = st.checkbox("🤖 Incluir análisis de IA", value=True)
    smart_query_sidebar = st.checkbox("🧠 Activar búsqueda inteligente con IA (Groq)", value=True,
        help="Reescribe tu consulta en español, corrige errores y busca con mayor precisión")
    
    # Configuración de recomendaciones
    st.header("📊 Recomendaciones")
    preferred_genres = st.multiselect(
        "Géneros preferidos:",
        ["Dramas", "Comedies", "Action & Adventure", "Thrillers", "Horror Movies"],
        default=["Dramas", "Thrillers"]
    )
    
    year_range = st.slider(
        "Rango de años:",
        min_value=1900,
        max_value=2024,
        value=(2020, 2024)
    )

    st.header("🧹 Trailers en CSV")
    max_to_update = st.number_input(
        "Máximo a actualizar en esta ejecución",
        min_value=1,
        max_value=200,
        value=20,
        step=1,
        help="Buscar y guardar trailers faltantes en la columna trailer_url del CSV"
    )
    if st.button("🔄 Actualizar/forzar búsqueda de trailers", type="secondary"):
        with st.spinner("Buscando y guardando trailers faltantes en el CSV..."):
            try:
                summary = search_service.fill_trailer_urls(int(max_to_update))
                if summary.get('updated', 0) > 0:
                    st.success(
                        f"✅ Trailers actualizados: {summary['updated']} | Fallidos: {summary['failed']} | "
                        f"Faltantes antes: {summary['total_missing_before']} → después: {summary.get('total_missing_after', 'N/A')}"
                    )
                else:
                    msg = summary.get('message') or "No se actualizaron trailers"
                    st.info(
                        f"ℹ️ {msg}. Faltantes: {summary.get('total_missing_before', 'N/A')}"
                    )
            except Exception as e:
                st.error(f"❌ Error al completar trailers: {str(e)}")

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["🔍 Búsqueda", "📊 Recomendaciones", "📈 Estadísticas"])

with tab1:
    st.header("🔍 Búsqueda de Títulos")
    
    # Búsqueda simple
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_input("Buscar títulos:", placeholder="Ej: comedy, action, drama...")
    
    with col2:
        search_type = st.selectbox(
            "Tipo de búsqueda:",
            ["all", "title", "director", "cast", "description", "country", "listed_in"]
        )
    
    limit = st.slider("Número de resultados:", min_value=5, max_value=50, value=10)

    st.markdown("---")
    st.subheader("🧠 Búsqueda con IA (Groq)")
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        ai_query = st.text_input("Describe lo que buscas (en español, con errores si hace falta):", placeholder="Quiero algo de balando con tom kruz de accion")
    with col_g2:
        analyze_limit = st.slider("Títulos a analizar (0-20)", min_value=0, max_value=20, value=10)
    smart_mode = st.checkbox("Usar búsqueda inteligente con IA (corrección agresiva)", value=True)
    confirm_interpretation = st.checkbox("Pedir confirmación de la consulta interpretada", value=True)
    
    if st.button("🧠 Buscar con IA", type="primary"):
        if ai_query:
            with st.spinner("Interpretando tu consulta con IA y buscando títulos..."):
                try:
                    # Primero ejecutamos una búsqueda normal pero con smart_query activado
                    request = SearchRequest(
                        query=ai_query,
                        search_type="all",
                        limit=limit,
                        include_trailers=include_trailers,
                        include_analysis=include_analysis,
                        smart_query=smart_query_sidebar or smart_mode
                    )
                    results = search_service.search_titles(request)

                    # Si se solicitó confirmación, volver a pedir interpretación explícita con Groq (si disponible)
                    interpreted_query_text = None
                    if confirm_interpretation and hasattr(search_service.ai_service, 'groq_client') and search_service.ai_service.groq_client:
                        try:
                            prompt = (
                                "Usuario en español describe búsqueda. Devuelve SOLO JSON: {normalized_query_es, notas_es}. "
                                f"Consulta: {ai_query}"
                            )
                            comp = search_service.ai_service.groq_client.chat.completions.create(
                                model="llama-3.1-8b-instant",
                                messages=[
                                    {"role": "system", "content": "Eres un asistente que devuelve JSON válido."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.2,
                                max_tokens=160,
                            )
                            import json
                            data = json.loads(comp.choices[0].message.content)
                            interpreted_query_text = data.get('normalized_query_es')
                        except Exception:
                            interpreted_query_text = None

                    if interpreted_query_text:
                        st.info(f"Consulta interpretada: {interpreted_query_text}")
                        if st.button("🔁 Reinterpretar con IA"):
                            st.experimental_rerun()

                    st.success(f"✅ Encontrados {results.total_count} resultados (IA)")
                    # Mostrar resultados (idéntico a la búsqueda normal)
                    for i, result in enumerate(results.results[:analyze_limit or len(results.results)]):
                        with st.expander(f"🎬 {result.title.title}", expanded=i < 3):
                            col1b, col2b = st.columns([2, 1])
                            with col1b:
                                st.write(f"**Título:** {result.title.title}")
                                st.write(f"**Tipo:** {result.title.type}")
                                if result.title.director:
                                    st.write(f"**Director:** {result.title.director}")
                                if result.title.release_year:
                                    st.write(f"**Año:** {result.title.release_year}")
                                if result.analysis and hasattr(result.analysis, 'recommendation_score'):
                                    st.write(
                                        f"**Calificación:** {render_star_rating(result.analysis.recommendation_score)} "
                                        f"({result.analysis.recommendation_score * 5:.1f}/5)"
                                    )
                                if result.title.listed_in:
                                    st.write(f"**Géneros:** {result.title.listed_in}")
                                if result.title.description:
                                    st.write(f"**Descripción:** {result.title.description}")
                            with col2b:
                                st.write("🎬 **Trailer:**")
                                if result.trailer:
                                    embed_html = f"""
                                    <iframe width=\"280\" height=\"157\" 
                                            src=\"https://www.youtube.com/embed/{result.trailer.video_id}?si=5DQfQXm4_CD13NpV\" 
                                            title=\"YouTube video player\" 
                                            frameborder=\"0\" 
                                            allow=\"accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share\" 
                                            referrerpolicy=\"strict-origin-when-cross-origin\" 
                                            allowfullscreen>
                                    </iframe>
                                    """
                                    st.components.v1.html(embed_html, height=180)
                                else:
                                    default_embed_html = """
                                    <iframe width=\"280\" height=\"157\" 
                                            src=\"https://www.youtube.com/embed/nb_fFj_0rq8?si=5DQfQXm4_CD13NpV\" 
                                            title=\"YouTube video player\" 
                                            frameborder=\"0\" 
                                            allow=\"accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share\" 
                                            referrerpolicy=\"strict-origin-when-cross-origin\" 
                                            allowfullscreen>
                                    </iframe>
                                    """
                                    st.components.v1.html(default_embed_html, height=180)
                                if result.analysis:
                                    st.write("🤖 **Análisis de IA:**")
                                    st.write(f"**Sentimiento:** {result.analysis.sentiment_score:.2f}")
                                    if result.analysis.genre_prediction:
                                        st.write(f"**Géneros predichos:** {', '.join(result.analysis.genre_prediction)}")
                                    st.write(f"**Audiencia:** {result.analysis.target_audience}")
                                    if result.analysis.content_warnings:
                                        st.write(f"**Advertencias:** {', '.join(result.analysis.content_warnings)}")
                                    st.write(
                                        f"**Calificación (IA):** {render_star_rating(result.analysis.recommendation_score)} "
                                        f"({result.analysis.recommendation_score * 5:.1f}/5)"
                                    )
                                    # Crítica corta (ocultable)
                                    if getattr(result.analysis, 'critique', None):
                                        with st.expander("📝 Ver crítica corta (IA)", expanded=False):
                                            st.write(result.analysis.critique)
                            st.markdown("---")
                except Exception as e:
                    st.error(f"❌ Error en la búsqueda con IA: {str(e)}")
    
    if st.button("🔍 Buscar", type="primary"):
        if query:
            with st.spinner("Buscando títulos..."):
                try:
                    request = SearchRequest(
                        query=query,
                        search_type=search_type,
                        limit=limit,
                        include_trailers=include_trailers,
                        include_analysis=include_analysis
                    )
                    
                    results = search_service.search_titles(request)
                    
                    st.success(f"✅ Encontrados {results.total_count} resultados")
                    
                    # Mostrar resultados
                    for i, result in enumerate(results.results):
                        with st.expander(f"🎬 {result.title.title}", expanded=i < 3):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**Título:** {result.title.title}")
                                st.write(f"**Tipo:** {result.title.type}")
                                if result.title.director:
                                    st.write(f"**Director:** {result.title.director}")
                                if result.title.cast:
                                    st.write(f"**Reparto:** {result.title.cast}")
                                if result.title.country:
                                    st.write(f"**País:** {result.title.country}")
                                if result.title.release_year:
                                    st.write(f"**Año:** {result.title.release_year}")
                                # Calificación en estrellas basada en recommendation_score si hay análisis
                                if result.analysis and hasattr(result.analysis, 'recommendation_score'):
                                    st.write(
                                        f"**Calificación:** {render_star_rating(result.analysis.recommendation_score)} "
                                        f"({result.analysis.recommendation_score * 5:.1f}/5)"
                                    )
                                if result.title.rating:
                                    st.write(f"**Rating:** {result.title.rating}")
                                if result.title.listed_in:
                                    st.write(f"**Géneros:** {result.title.listed_in}")
                                if result.title.description:
                                    st.write(f"**Descripción:** {result.title.description}")
                            
                            with col2:
                                # Mostrar trailer si está disponible
                                if result.trailer:
                                    st.write("🎬 **Trailer:**")
                                    embed_html = f"""
                                    <iframe width="280" height="157" 
                                            src="https://www.youtube.com/embed/{result.trailer.video_id}?si=5DQfQXm4_CD13NpV" 
                                            title="YouTube video player" 
                                            frameborder="0" 
                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                                            referrerpolicy="strict-origin-when-cross-origin" 
                                            allowfullscreen>
                                    </iframe>
                                    """
                                    st.components.v1.html(embed_html, height=180)
                                    if getattr(result.trailer, 'duration', None):
                                        st.write(f"**Duración:** {result.trailer.duration}")
                                    if getattr(result.trailer, 'view_count', None) is not None:
                                        st.write(f"**Vistas:** {result.trailer.view_count:,}")
                                else:
                                    # Si no hay objeto trailer, intentar usar 'trailer_url' del dataset si existe
                                    if hasattr(result, 'title') and hasattr(result.title, 'title'):
                                        # No tenemos acceso directo a la fila aquí; el servicio llena el objeto trailer si puede
                                        # Por lo tanto, si no hay trailer, mostramos el por defecto
                                        st.write("🎬 **Trailer:**")
                                        default_embed_html = """
                                        <iframe width="280" height="157" 
                                                src="https://www.youtube.com/embed/nb_fFj_0rq8?si=5DQfQXm4_CD13NpV" 
                                                title="YouTube video player" 
                                                frameborder="0" 
                                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                                                referrerpolicy="strict-origin-when-cross-origin" 
                                                allowfullscreen>
                                        </iframe>
                                        """
                                        st.components.v1.html(default_embed_html, height=180)
                                
                                # Mostrar análisis de IA si está disponible
                                if result.analysis:
                                    st.write("🤖 **Análisis de IA:**")
                                    st.write(f"**Sentimiento:** {result.analysis.sentiment_score:.2f}")
                                    if result.analysis.genre_prediction:
                                        st.write(f"**Géneros predichos:** {', '.join(result.analysis.genre_prediction)}")
                                    st.write(f"**Audiencia:** {result.analysis.target_audience}")
                                    if result.analysis.content_warnings:
                                        st.write(f"**Advertencias:** {', '.join(result.analysis.content_warnings)}")
                                    st.write(
                                        f"**Calificación (IA):** {render_star_rating(result.analysis.recommendation_score)} "
                                        f"({result.analysis.recommendation_score * 5:.1f}/5)"
                                    )
                            
                            st.markdown("---")
                except Exception as e:
                    st.error(f"❌ Error en la búsqueda: {str(e)}")
        else:
            st.warning("⚠️ Por favor ingresa un término de búsqueda")

with tab2:
    st.header("📊 Recomendaciones Personalizadas")
    
    if st.button("🎯 Obtener Recomendaciones", type="primary"):
        with st.spinner("Generando recomendaciones..."):
            try:
                preferences = UserPreferences(
                    preferred_genres=preferred_genres,
                    preferred_years=year_range,
                    include_trailers=include_trailers,
                    include_analysis=include_analysis
                )
                
                rec_request = RecommendationRequest(
                    preferences=preferences,
                    limit=10
                )
                
                recommendations = search_service.get_recommendations(rec_request)
                
                st.success(f"✅ {recommendations.total_count} recomendaciones generadas")
                
                for i, rec in enumerate(recommendations.recommendations):
                    header_suffix = ""
                    if rec.analysis:
                        header_suffix = f" — Calificación: {render_star_rating(rec.analysis.recommendation_score)} ({rec.analysis.recommendation_score * 5:.1f}/5)"
                    with st.expander(f"🎬 {rec.title.title}{header_suffix}", expanded=i < 3):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Título:** {rec.title.title}")
                            st.write(f"**Tipo:** {rec.title.type}")
                            if rec.title.director:
                                st.write(f"**Director:** {rec.title.director}")
                            if rec.title.release_year:
                                st.write(f"**Año:** {rec.title.release_year}")
                            if rec.analysis:
                                st.write(
                                    f"**Calificación:** {render_star_rating(rec.analysis.recommendation_score)} "
                                    f"({rec.analysis.recommendation_score * 5:.1f}/5)"
                                )
                            if rec.title.listed_in:
                                st.write(f"**Géneros:** {rec.title.listed_in}")
                        
                        with col2:
                            # Mostrar trailer embebido
                            st.write("🎬 **Trailer:**")
                            if rec.trailer:
                                embed_html = f"""
                                <iframe width="280" height="157" 
                                        src="https://www.youtube.com/embed/{rec.trailer.video_id}?si=5DQfQXm4_CD13NpV" 
                                        title="YouTube video player" 
                                        frameborder="0" 
                                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                                        referrerpolicy="strict-origin-when-cross-origin" 
                                        allowfullscreen>
                                </iframe>
                                """
                                st.components.v1.html(embed_html, height=180)
                            else:
                                # Mostrar trailer por defecto de Avatar
                                default_embed_html = """
                                <iframe width="280" height="157" 
                                        src="https://www.youtube.com/embed/nb_fFj_0rq8?si=5DQfQXm4_CD13NpV" 
                                        title="YouTube video player" 
                                        frameborder="0" 
                                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                                        referrerpolicy="strict-origin-when-cross-origin" 
                                        allowfullscreen>
                                </iframe>
                                """
                                st.components.v1.html(default_embed_html, height=180)
                            
                            if rec.analysis:
                                st.write("🤖 **Análisis:**")
                                st.write(f"**Sentimiento:** {rec.analysis.sentiment_score:.2f}")
                                if rec.analysis.genre_prediction:
                                    st.write(f"**Géneros:** {', '.join(rec.analysis.genre_prediction)}")
                                st.write(f"**Audiencia:** {rec.analysis.target_audience}")
                                if getattr(rec.analysis, 'critique', None):
                                    with st.expander("📝 Ver crítica corta (IA)", expanded=False):
                                        st.write(rec.analysis.critique)
                        
                        st.markdown("---")
            except Exception as e:
                st.error(f"❌ Error al generar recomendaciones: {str(e)}")

with tab3:
    st.header("📈 Estadísticas del Dataset")
    
    try:
        stats = search_service.get_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Títulos", f"{stats['total_titles']:,}")
            st.metric("Películas", f"{stats['movies']:,}")
        
        with col2:
            st.metric("Series de TV", f"{stats['tv_shows']:,}")
            st.metric("Países", f"{stats['countries']:,}")
        
        with col3:
            if 'years_range' in stats:
                st.metric("Año Mínimo", stats['years_range']['min'])
                st.metric("Año Máximo", stats['years_range']['max'])
        
        # Gráfico de distribución por tipo
        if 'movies' in stats and 'tv_shows' in stats:
            import plotly.express as px
            
            data = {
                'Tipo': ['Películas', 'Series de TV'],
                'Cantidad': [stats['movies'], stats['tv_shows']]
            }
            
            fig = px.pie(data, values='Cantidad', names='Tipo', title='Distribución por Tipo')
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Error al cargar estadísticas: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🎬 Netflix Titles Search v2.0 | Con IA y YouTube Integration</p>
</div>
""", unsafe_allow_html=True)
