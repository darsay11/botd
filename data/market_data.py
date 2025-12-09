"""
Módulo para gestión de datos de mercado.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

import MetaTrader5 as mt5

from core.exceptions import ErrorMercado

@dataclass
class Vela:
    """Representa una vela de precios."""
    timestamp: datetime
    apertura: float
    alto: float
    bajo: float
    cierre: float
    volumen: int
    simbolo: str
    timeframe: str

class MarketData:
    """Gestor de datos de mercado."""
    
    # Mapeo de timeframes a MT5
    TIMEFRAMES_MT5 = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1
    }
    
    def __init__(self, config):
        """Inicializa el gestor de datos."""
        self.config = config
        self.simbolo = config['general']['simbolo']
        self.conexion_activa = False
        
        # Cache de datos
        self.cache_velas: Dict[str, pd.DataFrame] = {}
        self.ultima_actualizacion: Dict[str, datetime] = {}
        
    def conectar_mt5(self) -> bool:
        """Establece conexión con MT5."""
        try:
            config_mt5 = self.config.obtener_config_mt5()
            
            if not mt5.initialize(
                path=config_mt5.ruta_terminal,
                login=config_mt5.login,
                password=config_mt5.password,
                server=config_mt5.servidor
            ):
                logger.error(f"Error inicializando MT5: {mt5.last_error()}")
                return False
            
            self.conexion_activa = True
            logger.info(f"Conectado a MT5: {config_mt5.servidor}")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a MT5: {e}")
            raise ErrorMercado(f"Error conectando a MT5: {e}")
    
    def desconectar_mt5(self):
        """Cierra conexión con MT5."""
        if self.conexion_activa:
            mt5.shutdown()
            self.conexion_activa = False
            logger.info("Desconectado de MT5")
    
    def descargar_velas(
        self, 
        simbolo: str, 
        timeframe: str, 
        numero_velas: int = 500
    ) -> pd.DataFrame:
        """
        Descarga velas históricas desde MT5.
        
        Args:
            simbolo: Símbolo del instrumento
            timeframe: Timeframe (M1, M5, H1, etc.)
            numero_velas: Número de velas a descargar
            
        Returns:
            DataFrame con las velas
        """
        try:
            if not self.conexion_activa and not self.conectar_mt5():
                raise ErrorMercado("No hay conexión a MT5")
            
            # Obtener timeframe MT5
            tf_mt5 = self.TIMEFRAMES_MT5.get(timeframe)
            if tf_mt5 is None:
                raise ValueError(f"Timeframe no soportado: {timeframe}")
            
            # Descargar velas
            velas = mt5.copy_rates_from_pos(simbolo, tf_mt5, 0, numero_velas)
            
            if velas is None:
                raise ErrorMercado(f"No se pudieron descargar velas para {simbolo} {timeframe}")
            
            # Convertir a DataFrame
            df = pd.DataFrame(velas)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.rename(columns={
                'time': 'timestamp',
                'open': 'apertura',
                'high': 'alto',
                'low': 'bajo',
                'close': 'cierre',
                'tick_volume': 'volumen',
                'spread': 'spread',
                'real_volume': 'volumen_real'
            }, inplace=True)
            
            # Añadir columnas calculadas
            df['retorno'] = df['cierre'].pct_change()
            df['rango'] = df['alto'] - df['bajo']
            df['rango_pct'] = df['rango'] / df['apertura']
            
            # Actualizar cache
            cache_key = f"{simbolo}_{timeframe}"
            self.cache_velas[cache_key] = df
            self.ultima_actualizacion[cache_key] = datetime.now()
            
            logger.debug(f"Descargadas {len(df)} velas para {simbolo} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error descargando velas: {e}")
            raise ErrorMercado(f"Error descargando velas: {e}")
    
    def obtener_velas_multi_timeframe(
        self, 
        simbolo: str, 
        timeframes: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """
        Obtiene velas para múltiples timeframes.
        
        Args:
            simbolo: Símbolo del instrumento
            timeframes: Lista de timeframes a descargar
            
        Returns:
            Diccionario con DataFrames por timeframe
        """
        datos = {}
        
        for tf in timeframes:
            try:
                df = self.descargar_velas(simbolo, tf)
                datos[tf] = df
            except Exception as e:
                logger.warning(f"Error obteniendo {tf}: {e}")
                # Si hay error, usar cache si existe
                cache_key = f"{simbolo}_{tf}"
                if cache_key in self.cache_velas:
                    datos[tf] = self.cache_velas[cache_key]
        
        return datos
    
    def obtener_datos_actualizados(self) -> Dict[str, pd.DataFrame]:
        """
        Obtiene datos actualizados para todos los timeframes configurados.
        """
        timeframes = [
            self.config['timeframes']['principal'],
            self.config['timeframes']['confirmacion'],
            self.config['timeframes']['entrada'],
            self.config['timeframes']['tick']
        ]
        
        return self.obtener_velas_multi_timeframe(self.simbolo, timeframes)
    
    def obtener_precio_tick(self, simbolo: str = None) -> Dict:
        """
        Obtiene el último tick para un símbolo.
        
        Args:
            simbolo: Símbolo (None para usar el configurado)
            
        Returns:
            Diccionario con información del tick
        """
        if simbolo is None:
            simbolo = self.simbolo
        
        try:
            if not self.conexion_activa and not self.conectar_mt5():
                raise ErrorMercado("No hay conexión a MT5")
            
            tick = mt5.symbol_info_tick(simbolo)
            
            if tick is None:
                raise ErrorMercado(f"No se pudo obtener tick para {simbolo}")
            
            return {
                'simbolo': simbolo,
                'timestamp': datetime.now(),
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'volumen': tick.volume,
                'spread': tick.ask - tick.bid
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo tick: {e}")
            raise ErrorMercado(f"Error obteniendo tick: {e}")
    
    def normalizar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza un DataFrame de velas.
        
        Args:
            df: DataFrame de entrada
            
        Returns:
            DataFrame normalizado
        """
        # Verificar columnas requeridas
        columnas_requeridas = ['timestamp', 'apertura', 'alto', 'bajo', 'cierre', 'volumen']
        
        for col in columnas_requeridas:
            if col not in df.columns:
                raise ValueError(f"Columna requerida no encontrada: {col}")
        
        # Ordenar por timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Eliminar duplicados
        df = df.drop_duplicates(subset=['timestamp'])
        
        # Completar valores faltantes
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        return df
    
    def calcular_metricas_basicas(self, df: pd.DataFrame) -> Dict:
        """
        Calcula métricas básicas de mercado.
        
        Args:
            df: DataFrame con velas
            
        Returns:
            Diccionario con métricas
        """
        if len(df) < 2:
            return {}
        
        ultimo = df.iloc[-1]
        penultimo = df.iloc[-2]
        
        return {
            'precio_actual': ultimo['cierre'],
            'variacion_abs': ultimo['cierre'] - penultimo['cierre'],
            'variacion_pct': (ultimo['cierre'] / penultimo['cierre'] - 1) * 100,
            'volumen_promedio': df['volumen'].mean(),
            'volatilidad_promedio': df['rango_pct'].mean() * 100,
            'rango_dia': df['alto'].max() - df['bajo'].min(),
            'tendencia_corta': 'alcista' if ultimo['cierre'] > df['cierre'].iloc[-5] else 'bajista'
        }
    
    def __del__(self):
        """Destructor - cierra conexión."""
        self.desconectar_mt5()