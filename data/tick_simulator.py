"""
Simulador de ticks para backtesting.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

class TickSimulator:
    """
    Simula ticks a partir de datos de velas para backtesting.
    """
    
    def __init__(self, datos_velas: pd.DataFrame, spread: float = 0.0002):
        """
        Inicializa el simulador.
        
        Args:
            datos_velas: DataFrame con velas
            spread: Spread en puntos
        """
        self.datos_velas = datos_velas.copy()
        self.spread = spread
        self.ticks_generados = []
        self.indice_actual = 0
        
        # Preparar datos
        self._preparar_datos()
        
    def _preparar_datos(self):
        """Prepara los datos para la simulación."""
        # Verificar columnas requeridas
        columnas_requeridas = ['timestamp', 'apertura', 'alto', 'bajo', 'cierre']
        
        for col in columnas_requeridas:
            if col not in self.datos_velas.columns:
                raise ValueError(f"Columna requerida no encontrada: {col}")
        
        # Calcular volatilidad de cada vela
        self.datos_velas['rango'] = self.datos_velas['alto'] - self.datos_velas['bajo']
        self.datos_velas['volatilidad'] = self.datos_velas['rango'].rolling(20).mean().fillna(self.datos_velas['rango'].mean())
        
        # Estimar número de ticks por vela basado en volatilidad
        self.datos_velas['ticks_por_vela'] = np.clip(
            (self.datos_velas['volatilidad'] * 10000).astype(int),
            5, 100  # Entre 5 y 100 ticks por vela
        )
        
    def generar_ticks_para_vela(self, vela_idx: int) -> List[Dict]:
        """
        Genera ticks para una vela específica.
        
        Args:
            vela_idx: Índice de la vela
            
        Returns:
            Lista de ticks generados
        """
        if vela_idx >= len(self.datos_velas):
            return []
        
        vela = self.datos_velas.iloc[vela_idx]
        ticks_por_vela = int(vela['ticks_por_vela'])
        
        ticks = []
        tiempo_inicio = vela['timestamp']
        
        # Generar precio base con ruido browniano
        precios = np.linspace(vela['apertura'], vela['cierre'], ticks_por_vela)
        
        # Añadir ruido proporcional a la volatilidad
        ruido = np.random.normal(0, vela['volatilidad'] * 0.1, ticks_por_vela)
        precios_con_ruido = precios + ruido
        
        # Asegurar que los precios estén dentro del rango de la vela
        precios_con_ruido = np.clip(precios_con_ruido, vela['bajo'], vela['alto'])
        
        # Generar ticks
        for i in range(ticks_por_vela):
            # Calcular tiempo para este tick
            tiempo_offset = timedelta(seconds=(i * 60) / ticks_por_vela)
            timestamp = tiempo_inicio + tiempo_offset
            
            # Precio bid y ask
            bid = precios_con_ruido[i]
            ask = bid + self.spread
            
            tick = {
                'timestamp': timestamp,
                'bid': bid,
                'ask': ask,
                'last': (bid + ask) / 2,
                'volumen': np.random.randint(1, 10),  # Volumen aleatorio
                'spread': self.spread
            }
            
            ticks.append(tick)
        
        return ticks
    
    def obtener_siguiente_tick(self) -> Optional[Dict]:
        """
        Obtiene el siguiente tick en la simulación.
        
        Returns:
            Diccionario con datos del tick o None si terminó
        """
        if self.indice_actual >= len(self.datos_velas):
            return None
        
        # Si no hay ticks generados para la vela actual, generarlos
        if not hasattr(self, 'ticks_actuales') or not self.ticks_actuales:
            self.ticks_actuales = self.generar_ticks_para_vela(self.indice_actual)
            self.tick_idx = 0
        
        # Si aún hay ticks en la vela actual
        if self.tick_idx < len(self.ticks_actuales):
            tick = self.ticks_actuales[self.tick_idx]
            self.tick_idx += 1
            self.ticks_generados.append(tick)
            return tick
        else:
            # Pasar a la siguiente vela
            self.indice_actual += 1
            self.ticks_actuales = []
            return self.obtener_siguiente_tick()
    
    def simular_todos_ticks(self) -> pd.DataFrame:
        """
        Simula todos los ticks y retorna un DataFrame.
        
        Returns:
            DataFrame con todos los ticks
        """
        todos_ticks = []
        
        while True:
            tick = self.obtener_siguiente_tick()
            if tick is None:
                break
            todos_ticks.append(tick)
        
        return pd.DataFrame(todos_ticks)
    
    def reset(self):
        """Reinicia el simulador."""
        self.indice_actual = 0
        self.ticks_actuales = []
        self.tick_idx = 0
        self.ticks_generados = []
    
    @property
    def progreso(self) -> float:
        """Obtiene el progreso de la simulación (0-1)."""
        if len(self.datos_velas) == 0:
            return 0.0
        return self.indice_actual / len(self.datos_velas)