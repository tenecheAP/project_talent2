#!/usr/bin/env python3
"""
Script de prueba para verificar que todas las funcionalidades de la aplicación funcionan correctamente
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Prueba las importaciones principales"""
    print("🔍 Probando importaciones...")
    
    try:
        from app.models import NetflixTitle, ContentAnalysis, VideoInfo, SearchRequest
        print("✅ Modelos Pydantic importados correctamente")
    except Exception as e:
        print(f"❌ Error importando modelos: {e}")
        return False
    
    try:
        from app.constants import COLUMNAS_BUSQUEDA, GENEROS_POPULARES
        print("✅ Constantes importadas correctamente")
    except Exception as e:
        print(f"❌ Error importando constantes: {e}")
        return False
    
    try:
        from app.data_loader import DataLoader
        print("✅ DataLoader importado correctamente")
    except Exception as e:
        print(f"❌ Error importando DataLoader: {e}")
        return False
    
    try:
        from app.services import NetflixSearchService
        print("✅ NetflixSearchService importado correctamente")
    except Exception as e:
        print(f"❌ Error importando NetflixSearchService: {e}")
        return False
    
    try:
        from app.ai_service import AIService
        print("✅ AIService importado correctamente")
    except Exception as e:
        print(f"❌ Error importando AIService: {e}")
        return False
    
    try:
        from app.youtube_service import YouTubeService
        print("✅ YouTubeService importado correctamente")
    except Exception as e:
        print(f"❌ Error importando YouTubeService: {e}")
        return False
    
    return True

def test_data_loading():
    """Prueba la carga de datos"""
    print("\n📊 Probando carga de datos...")
    
    try:
        from app.data_loader import DataLoader
        
        loader = DataLoader()
        df = loader.load_data()
        
        print(f"✅ Datos cargados: {len(df)} filas")
        print(f"✅ Columnas: {list(df.columns)}")
        
        # Probar información del dataset
        info = loader.get_data_info()
        print(f"✅ Información del dataset obtenida: {info['total_rows']} títulos")
        
        return True
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        traceback.print_exc()
        return False

def test_ai_service():
    """Prueba el servicio de IA"""
    print("\n🤖 Probando servicio de IA...")
    
    try:
        from app.ai_service import AIService
        from app.models import NetflixTitle
        
        ai_service = AIService()
        
        # Crear un título de prueba
        test_title = NetflixTitle(
            show_id="test1",
            type="Movie",
            title="Avatar",
            director="James Cameron",
            cast="Sam Worthington, Zoe Saldana",
            country="United States",
            release_year=2009,
            rating="PG-13",
            listed_in="Action & Adventure, Sci-Fi & Fantasy",
            description="A paraplegic marine dispatched to the moon Pandora on a unique mission becomes torn between following his orders and protecting the world he feels is his home."
        )
        
        # Analizar contenido
        analysis = ai_service.analyze_content(test_title)
        
        print(f"✅ Análisis de IA completado:")
        print(f"   - Sentimiento: {analysis.sentiment_score:.2f}")
        print(f"   - Géneros predichos: {analysis.genre_prediction}")
        print(f"   - Audiencia: {analysis.target_audience}")
        print(f"   - Score recomendación: {analysis.recommendation_score:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Error en servicio de IA: {e}")
        traceback.print_exc()
        return False

def test_search_service():
    """Prueba el servicio de búsqueda"""
    print("\n🔍 Probando servicio de búsqueda...")
    
    try:
        from app.data_loader import DataLoader
        from app.services import NetflixSearchService
        from app.models import SearchRequest
        
        # Cargar datos
        loader = DataLoader()
        df = loader.load_data()
        
        # Crear servicio de búsqueda
        search_service = NetflixSearchService(df)
        
        # Probar búsqueda
        request = SearchRequest(
            query="avatar",
            search_type="title",
            limit=5,
            include_trailers=False,
            include_analysis=True
        )
        
        results = search_service.search_titles(request)
        
        print(f"✅ Búsqueda completada: {results.total_count} resultados")
        
        if results.results:
            first_result = results.results[0]
            print(f"   - Primer resultado: {first_result.title.title}")
            if first_result.analysis:
                print(f"   - Análisis disponible: {first_result.analysis.sentiment_score:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Error en servicio de búsqueda: {e}")
        traceback.print_exc()
        return False

def test_youtube_service():
    """Prueba el servicio de YouTube"""
    print("\n🎥 Probando servicio de YouTube...")
    
    try:
        from app.youtube_service import YouTubeService
        
        youtube_service = YouTubeService()
        
        # Probar sin API key (debería devolver None)
        trailer = youtube_service.search_trailer("Avatar", 2009)
        
        if trailer is None:
            print("✅ Servicio de YouTube funciona correctamente (sin API key)")
        else:
            print("✅ Trailer encontrado (con API key configurada)")
        
        return True
    except Exception as e:
        print(f"❌ Error en servicio de YouTube: {e}")
        traceback.print_exc()
        return False

def test_visualization():
    """Prueba las librerías de visualización"""
    print("\n📈 Probando visualización...")
    
    try:
        import plotly.express as px
        import pandas as pd
        
        # Crear datos de prueba
        data = {
            'Tipo': ['Películas', 'Series de TV'],
            'Cantidad': [6131, 2676]
        }
        df = pd.DataFrame(data)
        
        # Crear gráfico
        fig = px.pie(df, values='Cantidad', names='Tipo', title='Distribución por Tipo')
        
        print("✅ Plotly funciona correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en visualización: {e}")
        traceback.print_exc()
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de la aplicación Netflix Titles Search")
    print("=" * 60)
    
    tests = [
        ("Importaciones", test_imports),
        ("Carga de datos", test_data_loading),
        ("Servicio de IA", test_ai_service),
        ("Servicio de búsqueda", test_search_service),
        ("Servicio de YouTube", test_youtube_service),
        ("Visualización", test_visualization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASÓ")
            else:
                print(f"❌ {test_name}: FALLÓ")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Resumen de pruebas: {passed}/{total} pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La aplicación está lista para usar.")
        print("\nPara ejecutar la aplicación:")
        print("   streamlit run main.py")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 