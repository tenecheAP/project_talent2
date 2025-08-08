import streamlit as st
import pandas as pd
from app.data_loader import DataLoader
from app.services import NetflixSearchService
from app.models import SearchRequest, UserPreferences, RecommendationRequest
from app.constants import columnas_busqueda

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
                                if result.title.rating:
                                    st.write(f"**Rating:** {result.title.rating}")
                                if result.title.listed_in:
                                    st.write(f"**Géneros:** {result.title.listed_in}")
                                if result.title.description:
                                    st.write(f"**Descripción:** {result.title.description}")
                            
                            with col2:
                                # Mostrar trailer si está disponible
                                if result.trailer:
                                    st.image(result.trailer.thumbnail_url, caption="Trailer")
                                    st.write(f"**Duración:** {result.trailer.duration}")
                                    st.write(f"**Vistas:** {result.trailer.view_count:,}")
                                
                                # Mostrar análisis de IA si está disponible
                                if result.analysis:
                                    st.write("🤖 **Análisis de IA:**")
                                    st.write(f"**Sentimiento:** {result.analysis.sentiment_score:.2f}")
                                    if result.analysis.genre_prediction:
                                        st.write(f"**Géneros predichos:** {', '.join(result.analysis.genre_prediction)}")
                                    st.write(f"**Audiencia:** {result.analysis.target_audience}")
                                    if result.analysis.content_warnings:
                                        st.write(f"**Advertencias:** {', '.join(result.analysis.content_warnings)}")
                                    st.write(f"**Score recomendación:** {result.analysis.recommendation_score:.2f}")
                            
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
                    with st.expander(f"🎬 {rec.title.title} (Score: {rec.analysis.recommendation_score:.2f})", expanded=i < 3):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Título:** {rec.title.title}")
                            st.write(f"**Tipo:** {rec.title.type}")
                            if rec.title.director:
                                st.write(f"**Director:** {rec.title.director}")
                            if rec.title.release_year:
                                st.write(f"**Año:** {rec.title.release_year}")
                            if rec.title.listed_in:
                                st.write(f"**Géneros:** {rec.title.listed_in}")
                        
                        with col2:
                            if rec.trailer:
                                st.image(rec.trailer.thumbnail_url, caption="Trailer")
                            
                            if rec.analysis:
                                st.write("🤖 **Análisis:**")
                                st.write(f"**Sentimiento:** {rec.analysis.sentiment_score:.2f}")
                                if rec.analysis.genre_prediction:
                                    st.write(f"**Géneros:** {', '.join(rec.analysis.genre_prediction)}")
                                st.write(f"**Audiencia:** {rec.analysis.target_audience}")
                        
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
