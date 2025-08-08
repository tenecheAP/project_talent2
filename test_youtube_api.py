#!/usr/bin/env python3
"""
Script para probar la API de YouTube v3
"""

import os
import requests
import json
from typing import Optional, Dict, Any

def test_youtube_api_key():
    """Prueba si la API key de YouTube está configurada"""
    print("🔑 Probando configuración de API key de YouTube...")
    
    # Verificar variables de entorno
    api_key_env = os.getenv("YOUTUBE_API_KEY")
    if api_key_env:
        print(f"✅ API key encontrada en variables de entorno: {api_key_env[:10]}...")
        return api_key_env
    
    # Verificar en config.py
    try:
        from app.config import CLAVE_API_YOUTUBE
        if CLAVE_API_YOUTUBE and CLAVE_API_YOUTUBE != "TU_API_KEY_AQUI":
            print(f"✅ API key encontrada en config.py: {CLAVE_API_YOUTUBE[:10]}...")
            return CLAVE_API_YOUTUBE
        else:
            print("⚠️  API key no configurada en config.py")
    except ImportError:
        print("❌ No se puede importar config.py")
    
    print("❌ No se encontró API key válida")
    return None

def test_youtube_api_connection(api_key: str) -> bool:
    """Prueba la conexión con la API de YouTube"""
    print(f"\n🌐 Probando conexión con YouTube API...")
    
    base_url = "https://www.googleapis.com/youtube/v3"
    
    # Parámetros de prueba
    params = {
        'part': 'snippet',
        'q': 'test video',
        'type': 'video',
        'maxResults': 1,
        'key': api_key
    }
    
    try:
        response = requests.get(f"{base_url}/search", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                print("✅ Conexión exitosa con YouTube API")
                print(f"   - Status: {response.status_code}")
                print(f"   - Resultados encontrados: {len(data['items'])}")
                return True
            else:
                print("⚠️  Conexión exitosa pero sin resultados")
                return True
        else:
            print(f"❌ Error en la API: {response.status_code}")
            print(f"   - Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_search_trailer(api_key: str) -> bool:
    """Prueba la búsqueda de trailers"""
    print(f"\n🎬 Probando búsqueda de trailers...")
    
    try:
        from app.youtube_service import YouTubeService
        
        youtube_service = YouTubeService(api_key)
        
        # Probar búsqueda de trailer
        trailer = youtube_service.search_trailer("Avatar", 2009)
        
        if trailer:
            print("✅ Trailer encontrado:")
            print(f"   - Título: {trailer.title}")
            print(f"   - ID: {trailer.video_id}")
            print(f"   - Canal: {trailer.channel_title}")
            print(f"   - Vistas: {trailer.view_count:,}")
            print(f"   - URL: {youtube_service.get_trailer_url(trailer.video_id)}")
            return True
        else:
            print("⚠️  No se encontró trailer (puede ser normal)")
            return True
            
    except Exception as e:
        print(f"❌ Error en búsqueda de trailer: {e}")
        return False

def test_video_details(api_key: str) -> bool:
    """Prueba obtener detalles de un video específico"""
    print(f"\n📹 Probando obtención de detalles de video...")
    
    # ID de un video de prueba (Avatar trailer)
    test_video_id = "d9MyWQRELM4"  # Avatar trailer
    
    base_url = "https://www.googleapis.com/youtube/v3"
    params = {
        'part': 'snippet,statistics,contentDetails',
        'id': test_video_id,
        'key': api_key
    }
    
    try:
        response = requests.get(f"{base_url}/videos", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                video = data['items'][0]
                snippet = video['snippet']
                statistics = video.get('statistics', {})
                
                print("✅ Detalles de video obtenidos:")
                print(f"   - Título: {snippet['title']}")
                print(f"   - Canal: {snippet['channelTitle']}")
                print(f"   - Vistas: {statistics.get('viewCount', 'N/A')}")
                print(f"   - Likes: {statistics.get('likeCount', 'N/A')}")
                return True
            else:
                print("⚠️  Video no encontrado")
                return False
        else:
            print(f"❌ Error obteniendo detalles: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error obteniendo detalles: {e}")
        return False

def test_api_quotas(api_key: str) -> bool:
    """Prueba las cuotas de la API"""
    print(f"\n📊 Probando cuotas de la API...")
    
    base_url = "https://www.googleapis.com/youtube/v3"
    
    # Hacer múltiples llamadas para verificar cuotas
    test_queries = ["avatar", "netflix", "movie", "trailer"]
    
    successful_calls = 0
    total_calls = len(test_queries)
    
    for query in test_queries:
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': 1,
            'key': api_key
        }
        
        try:
            response = requests.get(f"{base_url}/search", params=params, timeout=5)
            
            if response.status_code == 200:
                successful_calls += 1
                print(f"   ✅ Query '{query}': OK")
            elif response.status_code == 403:
                print(f"   ❌ Query '{query}': Cuota excedida")
                break
            else:
                print(f"   ⚠️  Query '{query}': Error {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Query '{query}': Error de conexión")
    
    success_rate = (successful_calls / total_calls) * 100
    print(f"   📈 Tasa de éxito: {success_rate:.1f}% ({successful_calls}/{total_calls})")
    
    return success_rate > 50

def main():
    """Función principal de pruebas de YouTube API"""
    print("🎥 Iniciando pruebas de YouTube API v3")
    print("=" * 50)
    
    # Probar configuración de API key
    api_key = test_youtube_api_key()
    
    if not api_key:
        print("\n❌ No se puede probar la API sin una clave válida")
        print("\nPara configurar la API key:")
        print("1. Ve a https://console.developers.google.com/")
        print("2. Crea un proyecto y habilita YouTube Data API v3")
        print("3. Crea credenciales (API Key)")
        print("4. Configura la variable de entorno YOUTUBE_API_KEY")
        print("   o actualiza app/config.py con tu clave")
        return False
    
    # Ejecutar pruebas
    tests = [
        ("Conexión API", lambda: test_youtube_api_connection(api_key)),
        ("Búsqueda Trailers", lambda: test_search_trailer(api_key)),
        ("Detalles Video", lambda: test_video_details(api_key)),
        ("Cuotas API", lambda: test_api_quotas(api_key))
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
    
    print("\n" + "=" * 50)
    print(f"📊 Resumen de pruebas YouTube API: {passed}/{total} pasaron")
    
    if passed == total:
        print("🎉 ¡YouTube API está funcionando correctamente!")
    elif passed >= total - 1:
        print("⚠️  La API funciona pero con algunas limitaciones")
    else:
        print("❌ La API tiene problemas significativos")
    
    return passed >= total - 1

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 