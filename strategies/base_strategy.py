"""
Clase base para estrategias de trading.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

@dataclass
class Señal:
    """Representa una señal de trading."""
    timestamp: str
    simbolo: str
    direccion: str  # COMPRA | VENTA
    fuerza: float  # 0-100
    precio_entrada: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    razon_entrada: str = ""
    confirmaciones: List[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.confirmaciones is None:
            self.confirmaciones = []
        if self.metadata is None:
            self.metadata = {}
    
    def agregar_confirmacion(self, confirmacion: str):
        """Agrega una confirmación a la señal."""
        self.confirmaciones.append(confirmacion)
        self.fuerza = min(100, self.fuerza + 10)  # Aumentar fuerza por confirmación
    
    def es_valida(self, fuerza_minima: float = 50) -> bool:
        """Verifica si la señal es válida."""
        return self.fuerza >= fuerza_minima

class BaseStrategy(ABC):
    """Clase base abstracta para todas las estrategias."""
    
    def __init__(self, config):
        """Inicializa la estrategia base."""
        self.config = config
        self.nombre = self.__class__.__name__
        self.historial_senales = []
        self.parametros = {}
        
        logger.info(f"Estrategia inicializada: {self.nombre}")
    
    @abstractmethod
    def analizar_mercado(self, datos_mercado: Dict) -> Dict:
        """
        Analiza los datos de mercado y genera indicadores.
        
        Args:
            datos_mercado: Diccionario con DataFrames por timeframe
            
        Returns:
            Diccionario con análisis
        """
        pass
    
    @abstractmethod
    def generar_senales(self, analisis: Dict) -> List[Señal]:
        """
        Genera señales de trading basadas en el análisis.
        
        Args:
            analisis: Resultado del análisis de mercado
            
        Returns:
            Lista de señales generadas
        """
        pass
    
    def filtrar_senales(
        self, 
        senales: List[Señal], 
        fuerza_minima: float = 50
    ) -> List[Señal]:
        """
        Filtra señales por criterios de calidad.
        
        Args:
            senales: Lista de señales a filtrar
            fuerza_minima: Fuerza mínima requerida
            
        Returns:
            Señales filtradas
        """
        senales_filtradas = []
        
        for senal in senales:
            if senal.es_valida(fuerza_minima):
                # Verificar confirmaciones mínimas
                if len(senal.confirmaciones) >= 2:  # Mínimo 2 confirmaciones
                    senales_filtradas.append(senal)
        
        return senales_filtradas
    
    def registrar_senal(self, senal: Señal):
        """Registra una señal en el historial."""
        self.historial_senales.append(senal)
        logger.debug(f"Señal registrada: {senal.direccion} {senal.simbolo} - Fuerza: {senal.fuerza}")
    
    def obtener_rendimiento_senales(self) -> Dict:
        """
        Calcula el rendimiento de las señales generadas.
        
        Returns:
            Diccionario con métricas de rendimiento
        """
        if not self.historial_senales:
            return {}
        
        total_senales = len(self.historial_senales)
        senales_compra = sum(1 for s in self.historial_senales if s.direccion == 'COMPRA')
        senales_venta = sum(1 for s in self.historial_senales if s.direccion == 'VENTA')
        
        return {
            'total_senales': total_senales,
            'senales_compra': senales_compra,
            'senales_venta': senales_venta,
            'ratio_compra_venta': senales_compra / senales_venta if senales_venta > 0 else float('inf'),
            'fuerza_promedio': sum(s.fuerza for s in self.historial_senales) / total_senales
        }
    
    def actualizar_parametros(self, nuevos_parametros: Dict):
        """
        Actualiza los parámetros de la estrategia.
        
        Args:
            nuevos_parametros: Diccionario con nuevos parámetros
        """
        self.parametros.update(nuevos_parametros)
        logger.info(f"Parámetros actualizados: {nuevos_parametros}")
    
    def reset(self):
        """Reinicia el estado de la estrategia."""
        self.historial_senales.clear()
        logger.info("Estrategia reiniciada")