import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from .config import CSV_FILE_PATH, CSV_ENCODING, CSV_SEPARATOR

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """Clase para cargar y manejar datos de Netflix"""
    
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or CSV_FILE_PATH
        self.df: Optional[pd.DataFrame] = None
    
    def load_data(self) -> pd.DataFrame:
        """Carga los datos del archivo CSV"""
        try:
            logger.info(f"Cargando datos desde: {self.file_path}")
            
            if not self.file_path.exists():
                raise FileNotFoundError(f"El archivo {self.file_path} no existe")
            
            # Cargar CSV
            self.df = pd.read_csv(
                self.file_path,
                encoding=CSV_ENCODING,
                sep=CSV_SEPARATOR
            )
            
            # Asegurar columna para URL de trailer
            if 'trailer_url' not in self.df.columns:
                self.df['trailer_url'] = ''
                logger.info("Columna 'trailer_url' agregada al DataFrame")

            # Columnas para resultados de IA (Groq)
            for col in ['sentiment_llm', 'score_llm', 'critique_llm']:
                if col not in self.df.columns:
                    self.df[col] = '' if col == 'critique_llm' else None
                    logger.info(f"Columna '{col}' agregada al DataFrame")

            # Limpiar datos
            self._clean_data()
            
            logger.info(f"Datos cargados exitosamente. Filas: {len(self.df)}")
            return self.df
            
        except Exception as e:
            logger.error(f"Error al cargar datos: {str(e)}")
            raise
    
    def _clean_data(self):
        """Limpia y prepara los datos"""
        if self.df is None:
            return
        
        # Eliminar filas duplicadas
        initial_rows = len(self.df)
        self.df = self.df.drop_duplicates()
        logger.info(f"Filas duplicadas eliminadas: {initial_rows - len(self.df)}")
        
        # Limpiar espacios en blanco
        for col in self.df.select_dtypes(include=['object']).columns:
            self.df[col] = self.df[col].str.strip()
        
        # Convertir release_year a numérico
        if 'release_year' in self.df.columns:
            self.df['release_year'] = pd.to_numeric(self.df['release_year'], errors='coerce')
        
        # Limpiar date_added
        if 'date_added' in self.df.columns:
            self.df['date_added'] = self.df['date_added'].str.strip()
    
    def get_data_info(self) -> Dict[str, Any]:
        """Obtiene información sobre los datos cargados"""
        if self.df is None:
            return {}
        
        info = {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'columns': list(self.df.columns),
            'data_types': self.df.dtypes.to_dict(),
            'missing_values': self.df.isnull().sum().to_dict(),
            'memory_usage': self.df.memory_usage(deep=True).sum()
        }
        
        # Estadísticas por tipo
        if 'type' in self.df.columns:
            info['type_distribution'] = self.df['type'].value_counts().to_dict()
        
        # Rango de años
        if 'release_year' in self.df.columns:
            info['year_range'] = {
                'min': int(self.df['release_year'].min()),
                'max': int(self.df['release_year'].max())
            }
        
        return info
    
    def get_sample_data(self, n: int = 5) -> pd.DataFrame:
        """Obtiene una muestra de los datos"""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df.sample(n=min(n, len(self.df)))
    
    def filter_by_type(self, content_type: str) -> pd.DataFrame:
        """Filtra datos por tipo de contenido"""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df[self.df['type'] == content_type]
    
    def filter_by_year_range(self, start_year: int, end_year: int) -> pd.DataFrame:
        """Filtra datos por rango de años"""
        if self.df is None or 'release_year' not in self.df.columns:
            return pd.DataFrame()
        
        mask = (self.df['release_year'] >= start_year) & (self.df['release_year'] <= end_year)
        return self.df[mask]

    def save_data(self) -> None:
        """Guarda el DataFrame actual al CSV de origen"""
        if self.df is None:
            return
        try:
            self.df.to_csv(self.file_path, index=False, encoding=CSV_ENCODING, sep=CSV_SEPARATOR)
            logger.info("Datos guardados con éxito en el CSV")
        except Exception as e:
            logger.error(f"Error al guardar datos en CSV: {str(e)}")

# Función legacy para compatibilidad
def cargar_datos_csv(path: str = "data/netflix_titles.csv") -> pd.DataFrame:
    """Función legacy para cargar datos CSV"""
    loader = DataLoader(Path(path))
    return loader.load_data()
