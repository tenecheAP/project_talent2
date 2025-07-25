import pandas as pd
from pydantic import BaseModel
from typing import List
import streamlit as st

# Carga el archivo CSV (ajusta el nombre del archivo si es necesario)
df = pd.read_csv('netflix_titles.csv')

# Selector de columna para búsqueda
columnas_busqueda = {
    "Título": "title",
    "Director": "director",
    "Reparto": "cast",
    "País": "country",
    "Año de lanzamiento": "release_year",
    "Género": "listed_in",
    "Tipo": "type"
}
columna_seleccionada = st.selectbox("Buscar por:", list(columnas_busqueda.keys()))
valor_busqueda = st.text_input(f'Buscar por {columna_seleccionada.lower()}:')
# Definir buscar_peliculas antes de llamarla
class Pelicula(BaseModel):
    title: str
    director: str
    cast: str
    country: str
    release_year: int
    listed_in: str
    type: str

def buscar_peliculas(columna, valor):
    resultados = df[df[columna].str.contains(valor, case=False, na=False)]
    peliculas = [
        Pelicula(
            title=str(row['title']) if pd.notnull(row['title']) else "",
            director=str(row['director']) if pd.notnull(row['director']) else "",
            cast=str(row['cast']) if pd.notnull(row['cast']) else "",
            country=str(row['country']) if pd.notnull(row['country']) else "",
            release_year=int(row['release_year']) if pd.notnull(row['release_year']) else 0,
            listed_in=str(row['listed_in']) if pd.notnull(row['listed_in']) else "",
            type=str(row['type']) if pd.notnull(row['type']) else ""
        )
        for _, row in resultados.head(10).iterrows()
    ]
    return peliculas

if valor_busqueda:
    columna = columnas_busqueda[columna_seleccionada]
    resultados = buscar_peliculas(columna, valor_busqueda)
    for peli in resultados:
        with st.container():
            st.markdown(f"### {peli.title}")
            st.write(f"**Director:** {peli.director}")
            st.write(f"**Reparto:** {peli.cast}")
            st.write(f"**País:** {peli.country}")
            st.write(f"**Año de lanzamiento:** {peli.release_year}")
            st.write(f"**Género:** {peli.listed_in}")
            st.write(f"**Tipo:** {peli.type}")
            st.markdown("---")

# Ejemplo de posibles búsquedas:
# - title: buscar por nombre de película o serie
# - director: buscar por director
# - cast: buscar por actor/actriz
# - country: buscar por país
# - release_year: buscar por año de lanzamiento
# - listed_in: buscar por género/categoría
# - type: buscar por tipo (Movie o TV Show)

class Pelicula(BaseModel):
    title: str
    director: str
    cast: str
    country: str
    release_year: int
    listed_in: str
    type: str

def buscar_peliculas(columna, valor):
    resultados = df[df[columna].str.contains(valor, case=False, na=False)]
    peliculas = [
        Pelicula(
            title=str(row['title']) if pd.notnull(row['title']) else "",
            director=str(row['director']) if pd.notnull(row['director']) else "",
            cast=str(row['cast']) if pd.notnull(row['cast']) else "",
            country=str(row['country']) if pd.notnull(row['country']) else "",
            release_year=int(row['release_year']) if pd.notnull(row['release_year']) else 0,
            listed_in=str(row['listed_in']) if pd.notnull(row['listed_in']) else "",
            type=str(row['type']) if pd.notnull(row['type']) else ""
        )
        for _, row in resultados.head(10).iterrows()
    ]
    return peliculas

# Frontend con Streamlit
st.title("Buscador de Películas de Netflix")
pelicula = st.text_input('Buscar películas por título:')
if pelicula:
    resultados = buscar_peliculas('title', pelicula)
    for peli in resultados:
        with st.container():
            st.markdown(f"### {peli.title}")
            st.write(f"**Director:** {peli.director}")
            st.write(f"**Reparto:** {peli.cast}")
            st.write(f"**País:** {peli.country}")
            st.write(f"**Año de lanzamiento:** {peli.release_year}")
            st.write(f"**Género:** {peli.listed_in}")
            st.write(f"**Tipo:** {peli.type}")
            st.markdown("---")