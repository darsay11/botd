"""
Generador de señales de trading.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from loguru import logger

from strategies.base_strategy import Señal

class SignalGenerator:
    """Genera señales de trading basadas en condiciones técnicas."""
    
    def __init__(self, config):
        """Inicializa el generador de señales."""
        self.config = config
        self.condiciones = self._construir_condiciones()
        
    def _construir_condiciones(self) -> List[Dict]:
        """Construye las condiciones para generar señales."""
        return [
            # Condición 1: Cruce de EMAs
            {
                'nombre': 'crossover_ema',
                'descripcion': 'Cruce alcista de EMA rápida sobre EMA lenta',
                'timeframe': 'entrada',
                'funcion': self._condicion_crossover_ema,
                'peso': 30
            },
            # Condición 2: RSI en zona de sobreventa/sobrecompra
            {
                'nombre': 'rsi_extremo',
                'descripcion': 'RSI en zona de sobreventa o sobrecompra',
                'timeframe': 'confirmacion',
                'funcion': self._condicion_rsi_extremo,
                'peso': 25
            },
            # Condición 3: Divergencia MACD
            {
                'nombre': 'divergencia_macd',
                'descripcion': 'Divergencia entre precio y MACD',
                'timeframe': 'principal',
                'funcion': self._condicion_divergencia_macd,
                'peso': 20
            },
            # Condición 4: Patrón de velas
            {
                'nombre': 'patron_velas',
                'descripcion': 'Patrón de velas japonés',
                'timeframe': 'entrada',
                'funcion': self._condicion_patron_velas,
                'peso': 15
            },
            # Condición 5: Volumen confirmatorio
            {
                'nombre': 'volumen_confirmatorio',
                'descripcion': 'Volumen por encima del promedio',
                'timeframe': 'entrada',
                'funcion': self._condicion_volumen,
                'peso': 10
            }
        ]
    
    def generar_senales(self, analisis: Dict) -> List[Señal]:
        """
        Genera señales basadas en condiciones técnicas.
        
        Args:
            analisis: Análisis completo del mercado
            
        Returns:
            Lista de señales generadas
        """
        senales = []
        
        try:
            # Evaluar cada condición
            condiciones_activadas = []
            
            for condicion in self.condiciones:
                resultado = self._evaluar_condicion(condicion, analisis)
                if resultado['activada']:
                    condiciones_activadas.append(resultado)
            
            # Generar señales basadas en condiciones activadas
            if condiciones_activadas:
                # Agrupar por dirección
                condiciones_compra = [c for c in condiciones_activadas if c['direccion'] == 'COMPRA']
                condiciones_venta = [c for c in condiciones_activadas if c['direccion'] == 'VENTA']
                
                # Generar señal de compra si hay condiciones suficientes
                if len(condiciones_compra) >= 2:
                    senal_compra = self._crear_senal_desde_condiciones('COMPRA', condiciones_compra, analisis)
                    if senal_compra:
                        senales.append(senal_compra)
                
                # Generar señal de venta si hay condiciones suficientes
                if len(condiciones_venta) >= 2:
                    senal_venta = self._crear_senal_desde_condiciones('VENTA', condiciones_venta, analisis)
                    if senal_venta:
                        senales.append(senal_venta)
            
            return senales
            
        except Exception as e:
            logger.error(f"Error generando señales: {e}")
            return []
    
    def _evaluar_condicion(self, condicion: Dict, analisis: Dict) -> Dict:
        """
        Evalúa una condición específica.
        
        Args:
            condicion: Condición a evaluar
            analisis: Análisis completo
            
        Returns:
            Resultado de la evaluación
        """
        try:
            # Obtener timeframe para esta condición
            tf_key = condicion['timeframe']
            tf_real = self.config['timeframes'][tf_key]
            
            if tf_real not in analisis:
                return {'activada': False, 'condicion': condicion['nombre']}
            
            # Evaluar condición
            resultado = condicion['funcion'](analisis[tf_real])
            
            if resultado['activada']:
                return {
                    'activada': True,
                    'condicion': condicion['nombre'],
                    'descripcion': condicion['descripcion'],
                    'direccion': resultado['direccion'],
                    'fuerza': condicion['peso'],
                    'metadata': resultado.get('metadata', {})
                }
            
            return {'activada': False, 'condicion': condicion['nombre']}
            
        except Exception as e:
            logger.warning(f"Error evaluando condición {condicion['nombre']}: {e}")
            return {'activada': False, 'condicion': condicion['nombre']}
    
    def _condicion_crossover_ema(self, analisis_tf: Dict) -> Dict:
        """Condición: Cruce de EMAs."""
        try:
            df = analisis_tf['dataframe']
            
            if len(df) < 3:
                return {'activada': False}
            
            # Obtener valores actuales y previos
            ema_rapida_actual = df['ema_9'].iloc[-1]
            ema_lenta_actual = df['ema_21'].iloc[-1]
            ema_rapida_anterior = df['ema_9'].iloc[-2]
            ema_lenta_anterior = df['ema_21'].iloc[-2]
            
            # Detectar crossover alcista
            if (ema_rapida_anterior <= ema_lenta_anterior and 
                ema_rapida_actual > ema_lenta_actual):
                return {
                    'activada': True,
                    'direccion': 'COMPRA',
                    'metadata': {
                        'ema_rapida': ema_rapida_actual,
                        'ema_lenta': ema_lenta_actual
                    }
                }
            
            # Detectar crossover bajista
            if (ema_rapida_anterior >= ema_lenta_anterior and 
                ema_rapida_actual < ema_lenta_actual):
                return {
                    'activada': True,
                    'direccion': 'VENTA',
                    'metadata': {
                        'ema_rapida': ema_rapida_actual,
                        'ema_lenta': ema_lenta_actual
                    }
                }
            
            return {'activada': False}
            
        except Exception as e:
            logger.warning(f"Error en condición crossover EMA: {e}")
            return {'activada': False}
    
    def _condicion_rsi_extremo(self, analisis_tf: Dict) -> Dict:
        """Condición: RSI en zona extrema."""
        try:
            rsi_actual = analisis_tf['rsi_actual']
            
            if rsi_actual is None:
                return {'activada': False}
            
            # RSI en sobreventa (potencial compra)
            if rsi_actual < 30:
                return {
                    'activada': True,
                    'direccion': 'COMPRA',
                    'metadata': {'rsi': rsi_actual}
                }
            
            # RSI en sobrecompra (potencial venta)
            if rsi_actual > 70:
                return {
                    'activada': True,
                    'direccion': 'VENTA',
                    'metadata': {'rsi': rsi_actual}
                }
            
            return {'activada': False}
            
        except Exception as e:
            logger.warning(f"Error en condición RSI: {e}")
            return {'activada': False}
    
    def _condicion_divergencia_macd(self, analisis_tf: Dict) -> Dict:
        """Condición: Divergencia entre precio y MACD."""
        try:
            df = analisis_tf['dataframe']
            
            if len(df) < 20:
                return {'activada': False}
            
            # Buscar divergencias en las últimas 20 velas
            precios = df['cierre'].values[-20:]
            macd_values = df['macd'].values[-20:]
            
            # Encontrar máximos y mínimos locales
            max_indices = self._encontrar_maximos_locales(precios)
            min_indices = self._encontrar_minimos_locales(precios)
            
            # Buscar divergencia alcista (precio hace mínimos más bajos, MACD hace mínimos más altos)
            if len(min_indices) >= 2:
                ultimo_min = min_indices[-1]
                penultimo_min = min_indices[-2]
                
                if (precios[ultimo_min] < precios[penultimo_min] and 
                    macd_values[ultimo_min] > macd_values[penultimo_min]):
                    return {
                        'activada': True,
                        'direccion': 'COMPRA',
                        'metadata': {
                            'tipo': 'divergencia_alcista',
                            'precio_actual': precios[-1]
                        }
                    }
            
            # Buscar divergencia bajista (precio hace máximos más altos, MACD hace máximos más bajos)
            if len(max_indices) >= 2:
                ultimo_max = max_indices[-1]
                penultimo_max = max_indices[-2]
                
                if (precios[ultimo_max] > precios[penultimo_max] and 
                    macd_values[ultimo_max] < macd_values[penultimo_max]):
                    return {
                        'activada': True,
                        'direccion': 'VENTA',
                        'metadata': {
                            'tipo': 'divergencia_bajista',
                            'precio_actual': precios[-1]
                        }
                    }
            
            return {'activada': False}
            
        except Exception as e:
            logger.warning(f"Error en condición divergencia MACD: {e}")
            return {'activada': False}
    
    def _condicion_patron_velas(self, analisis_tf: Dict) -> Dict:
        """Condición: Patrón de velas japonés."""
        try:
            df = analisis_tf['dataframe']
            
            if len(df) < 3:
                return {'activada': False}
            
            # Obtener últimas 3 velas
            vela_actual = df.iloc[-1]
            vela_anterior = df.iloc[-2]
            vela_anterior2 = df.iloc[-3]
            
            # Detectar martillo (señal de compra)
            cuerpo = abs(vela_actual['cierre'] - vela_actual['apertura'])
            sombra_superior = vela_actual['alto'] - max(vela_actual['apertura'], vela_actual['cierre'])
            sombra_inferior = min(vela_actual['apertura'], vela_actual['cierre']) - vela_actual['bajo']
            
            es_martillo = (sombra_inferior > cuerpo * 2 and 
                          sombra_superior < cuerpo * 0.3 and
                          vela_actual['cierre'] > vela_actual['apertura'])
            
            if es_martillo:
                return {
                    'activada': True,
                    'direccion': 'COMPRA',
                    'metadata': {'patron': 'martillo'}
                }
            
            # Detectar estrella fugaz (señal de venta)
            es_estrella_fugaz = (sombra_superior > cuerpo * 2 and 
                                sombra_inferior < cuerpo * 0.3 and
                                vela_actual['cierre'] < vela_actual['apertura'])
            
            if es_estrella_fugaz:
                return {
                    'activada': True,
                    'direccion': 'VENTA',
                    'metadata': {'patron': 'estrella_fugaz'}
                }
            
            # Detectar engulfing alcista
            es_engulfing_alcista = (vela_anterior['cierre'] < vela_anterior['apertura'] and
                                   vela_actual['cierre'] > vela_actual['apertura'] and
                                   vela_actual['apertura'] < vela_anterior['cierre'] and
                                   vela_actual['cierre'] > vela_anterior['apertura'])
            
            if es_engulfing_alcista:
                return {
                    'activada': True,
                    'direccion': 'COMPRA',
                    'metadata': {'patron': 'engulfing_alcista'}
                }
            
            # Detectar engulfing bajista
            es_engulfing_bajista = (vela_anterior['cierre'] > vela_anterior['apertura'] and
                                   vela_actual['cierre'] < vela_actual['apertura'] and
                                   vela_actual['apertura'] > vela_anterior['cierre'] and
                                   vela_actual['cierre'] < vela_anterior['apertura'])
            
            if es_engulfing_bajista:
                return {
                    'activada': True,
                    'direccion': 'VENTA',
                    'metadata': {'patron': 'engulfing_bajista'}
                }
            
            return {'activada': False}
            
        except Exception as e:
            logger.warning(f"Error en condición patron velas: {e}")
            return {'activada': False}
    
    def _condicion_volumen(self, analisis_tf: Dict) -> Dict:
        """Condición: Volumen confirmatorio."""
        try:
            volumen_alto = analisis_tf.get('volumen_alto', False)
            
            if volumen_alto:
                # Si hay volumen alto, considerar dirección basada en precio
                precio_actual = analisis_tf['precio_actual']
                df = analisis_tf['dataframe']
                
                if len(df) < 2:
                    return {'activada': False}
                
                precio_anterior = df['cierre'].iloc[-2]
                
                if precio_actual > precio_anterior:
                    return {
                        'activada': True,
                        'direccion': 'COMPRA',
                        'metadata': {'volumen_ratio': analisis_tf.get('volumen_ratio', 1)}
                    }
                else:
                    return {
                        'activada': True,
                        'direccion': 'VENTA',
                        'metadata': {'volumen_ratio': analisis_tf.get('volumen_ratio', 1)}
                    }
            
            return {'activada': False}
            
        except Exception as e:
            logger.warning(f"Error en condición volumen: {e}")
            return {'activada': False}
    
    def _encontrar_maximos_locales(self, array: np.ndarray, window: int = 3) -> List[int]:
        """Encuentra índices de máximos locales en un array."""
        maximos = []
        for i in range(window, len(array) - window):
            if (array[i] == max(array[i-window:i+window+1]) and 
                array[i] != array[i-window]):
                maximos.append(i)
        return maximos
    
    def _encontrar_minimos_locales(self, array: np.ndarray, window: int = 3) -> List[int]:
        """Encuentra índices de mínimos locales en un array."""
        minimos = []
        for i in range(window, len(array) - window):
            if (array[i] == min(array[i-window:i+window+1]) and 
                array[i] != array[i-window]):
                minimos.append(i)
        return minimos
    
    def _crear_senal_desde_condiciones(self, direccion: str, condiciones: List[Dict], 
                                       analisis: Dict) -> Señal:
        """
        Crea una señal a partir de condiciones activadas.
        
        Args:
            direccion: Dirección de la señal
            condiciones: Condiciones activadas
            analisis: Análisis completo
            
        Returns:
            Señal creada
        """
        try:
            # Calcular fuerza total
            fuerza_total = sum(c['fuerza'] for c in condiciones)
            
            # Obtener precio actual del timeframe de entrada
            tf_entrada = self.config['timeframes']['entrada']
            if tf_entrada in analisis:
                precio_actual = analisis[tf_entrada]['precio_actual']
            else:
                # Si no hay timeframe de entrada, usar el primero disponible
                primer_tf = list(analisis.keys())[0]
                precio_actual = analisis[primer_tf]['precio_actual']
            
            # Crear señal
            senal = Señal(
                timestamp=datetime.now().isoformat(),
                simbolo=self.config['general']['simbolo'],
                direccion=direccion,
                fuerza=min(100, fuerza_total),
                precio_entrada=precio_actual,
                razon_entrada=self._construir_razon_entrada(condiciones),
                confirmaciones=[c['condicion'] for c in condiciones],
                metadata={
                    'condiciones': [c['condicion'] for c in condiciones],
                    'fuerza_total': fuerza_total,
                    'timestamp_analisis': datetime.now().isoformat()
                }
            )
            
            return senal
            
        except Exception as e:
            logger.error(f"Error creando señal: {e}")
            return None
    
    def _construir_razon_entrada(self, condiciones: List[Dict]) -> str:
        """
        Construye la razón de entrada basada en condiciones.
        
        Args:
            condiciones: Condiciones activadas
            
        Returns:
            String con la razón
        """
        razones = []
        for cond in condiciones:
            razones.append(f"{cond['condicion']}: {cond['descripcion']}")
        
        return "; ".join(razones)