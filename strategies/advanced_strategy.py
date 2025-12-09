"""
Estrategia avanzada con detección de estructuras de mercado.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from loguru import logger

from strategies.base_strategy import BaseStrategy, Señal
from strategies.signal_generator import SignalGenerator

class AdvancedStrategy(BaseStrategy):
    """
    Estrategia avanzada que combina:
    - Análisis multi-timeframe
    - Indicadores técnicos
    - Detección de order blocks
    - Zonas de liquidez
    - Confirmaciones de volumen
    """
    
    def __init__(self, config):
        """Inicializa la estrategia avanzada."""
        super().__init__(config)
        self.generador_senales = SignalGenerator(config)
        self.ultimo_analisis = {}
        self.estructuras_detectadas = {
            'order_blocks': [],
            'zonas_liquidez': [],
            'soportes_resistencias': []
        }
        
        # Parámetros de la estrategia
        self.parametros.update({
            'fuerza_minima_senal': 60,
            'confirmaciones_minimas': 3,
            'max_senales_por_ciclo': 2,
            'filtro_tendencia_principal': True
        })
        
        logger.info("Estrategia avanzada inicializada")
    
    def analizar_mercado(self, datos_mercado: Dict) -> Dict:
        """
        Realiza análisis completo del mercado.
        
        Args:
            datos_mercado: Datos por timeframe
            
        Returns:
            Diccionario con análisis completo
        """
        try:
            analisis = {}
            
            # 1. Análisis por timeframe
            for tf, df in datos_mercado.items():
                if len(df) > 0:
                    analisis_tf = self._analizar_timeframe(df, tf)
                    analisis[tf] = analisis_tf
            
            # 2. Análisis multi-timeframe
            if len(analisis) >= 3:
                analisis['multi_tf'] = self._analizar_multi_timeframe(analisis)
            
            # 3. Detección de estructuras
            if 'H1' in analisis:
                df_h1 = datos_mercado.get('H1')
                if df_h1 is not None and len(df_h1) > 100:
                    self._detectar_estructuras(df_h1)
                    analisis['estructuras'] = self.estructuras_detectadas.copy()
            
            # 4. Tendencia general
            analisis['tendencia_general'] = self._determinar_tendencia(analisis)
            
            self.ultimo_analisis = analisis
            return analisis
            
        except Exception as e:
            logger.error(f"Error en análisis de mercado: {e}")
            return {}
    
    def _analizar_timeframe(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """
        Analiza un timeframe específico.
        
        Args:
            df: DataFrame con datos
            timeframe: Nombre del timeframe
            
        Returns:
            Diccionario con análisis
        """
        # Calcular indicadores básicos
        df_analisis = df.copy()
        
        # EMA
        df_analisis['ema_9'] = df_analisis['cierre'].ewm(span=9).mean()
        df_analisis['ema_21'] = df_analisis['cierre'].ewm(span=21).mean()
        df_analisis['ema_50'] = df_analisis['cierre'].ewm(span=50).mean()
        
        # RSI
        delta = df_analisis['cierre'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df_analisis['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df_analisis['cierre'].ewm(span=12).mean()
        ema_26 = df_analisis['cierre'].ewm(span=26).mean()
        df_analisis['macd'] = ema_12 - ema_26
        df_analisis['macd_signal'] = df_analisis['macd'].ewm(span=9).mean()
        
        # ATR
        high_low = df_analisis['alto'] - df_analisis['bajo']
        high_close = np.abs(df_analisis['alto'] - df_analisis['cierre'].shift())
        low_close = np.abs(df_analisis['bajo'] - df_analisis['cierre'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df_analisis['atr'] = true_range.rolling(window=14).mean()
        
        # Volumen
        df_analisis['volumen_sma'] = df_analisis['volumen'].rolling(window=20).mean()
        df_analisis['volumen_ratio'] = df_analisis['volumen'] / df_analisis['volumen_sma']
        
        # Determinar tendencia del timeframe
        precio_actual = df_analisis['cierre'].iloc[-1]
        tendencia = 'neutral'
        
        if precio_actual > df_analisis['ema_50'].iloc[-1]:
            if precio_actual > df_analisis['ema_21'].iloc[-1]:
                tendencia = 'alcista_fuerte'
            else:
                tendencia = 'alcista_debil'
        elif precio_actual < df_analisis['ema_50'].iloc[-1]:
            if precio_actual < df_analisis['ema_21'].iloc[-1]:
                tendencia = 'bajista_fuerte'
            else:
                tendencia = 'bajista_debil'
        
        return {
            'dataframe': df_analisis,
            'tendencia': tendencia,
            'precio_actual': precio_actual,
            'rsi_actual': df_analisis['rsi'].iloc[-1],
            'macd_actual': df_analisis['macd'].iloc[-1],
            'atr_actual': df_analisis['atr'].iloc[-1],
            'volumen_alto': df_analisis['volumen_ratio'].iloc[-1] > 1.5
        }
    
    def _analizar_multi_timeframe(self, analisis_por_tf: Dict) -> Dict:
        """
        Realiza análisis multi-timeframe.
        
        Args:
            analisis_por_tf: Análisis por timeframe
            
        Returns:
            Análisis multi-timeframe
        """
        mft_analysis = {
            'alineacion': False,
            'conflictos': [],
            'tendencia_conjunta': 'neutral',
            'fuerza_alineacion': 0
        }
        
        # Obtener tendencias de cada timeframe
        tendencias = {}
        for tf, analisis in analisis_por_tf.items():
            if 'tendencia' in analisis:
                tendencias[tf] = analisis['tendencia']
        
        # Verificar alineación
        if len(tendencias) >= 2:
            # Contar tendencias alcistas vs bajistas
            alcistas = sum(1 for t in tendencias.values() if 'alcista' in t)
            bajistas = sum(1 for t in tendencias.values() if 'bajista' in t)
            
            if alcistas > bajistas:
                mft_analysis['tendencia_conjunta'] = 'alcista'
                mft_analysis['fuerza_alineacion'] = alcistas / len(tendencias)
                mft_analysis['alineacion'] = alcistas >= 2
            elif bajistas > alcistas:
                mft_analysis['tendencia_conjunta'] = 'bajista'
                mft_analysis['fuerza_alineacion'] = bajistas / len(tendencias)
                mft_analysis['alineacion'] = bajistas >= 2
            
            # Identificar conflictos
            if alcistas > 0 and bajistas > 0:
                mft_analysis['conflictos'] = [tf for tf, t in tendencias.items() 
                                            if ('alcista' in t and mft_analysis['tendencia_conjunta'] == 'bajista') or
                                               ('bajista' in t and mft_analysis['tendencia_conjunta'] == 'alcista')]
        
        return mft_analysis
    
    def _detectar_estructuras(self, df: pd.DataFrame):
        """
        Detecta estructuras de mercado importantes.
        
        Args:
            df: DataFrame con datos del timeframe principal
        """
        try:
            # Resetear estructuras
            self.estructuras_detectadas = {
                'order_blocks': [],
                'zonas_liquidez': [],
                'soportes_resistencias': []
            }
            
            if len(df) < 100:
                return
            
            # Detectar Order Blocks
            self._detectar_order_blocks(df)
            
            # Detectar zonas de liquidez
            self._detectar_zonas_liquidez(df)
            
            # Detectar soportes y resistencias
            self._detectar_soportes_resistencias(df)
            
        except Exception as e:
            logger.error(f"Error detectando estructuras: {e}")
    
    def _detectar_order_blocks(self, df: pd.DataFrame):
        """
        Detecta order blocks en el gráfico.
        
        Un order block es una zona donde hubo gran actividad institucional.
        Se identifica por velas con volumen alto seguidas de una ruptura.
        """
        try:
            # Calcular volumen promedio
            volumen_promedio = df['volumen'].rolling(window=50).mean()
            
            # Identificar velas con volumen significativo (2x promedio)
            df['volumen_alto'] = df['volumen'] > (volumen_promedio * 2)
            
            # Buscar order blocks en las últimas 100 velas
            for i in range(2, min(100, len(df) - 5)):
                idx = -i
                
                # Verificar si es vela de volumen alto
                if df['volumen_alto'].iloc[idx]:
                    vela = df.iloc[idx]
                    
                    # Verificar ruptura en las siguientes velas
                    ruptura_alcista = False
                    ruptura_bajista = False
                    
                    for j in range(1, 6):
                        if idx + j >= len(df):
                            break
                        
                        if df['cierre'].iloc[idx + j] > vela['alto']:
                            ruptura_alcista = True
                        if df['cierre'].iloc[idx + j] < vela['bajo']:
                            ruptura_bajista = True
                    
                    # Si hubo ruptura, es un order block
                    if ruptura_alcista or ruptura_bajista:
                        order_block = {
                            'tipo': 'alcista' if ruptura_alcista else 'bajista',
                            'alto': vela['alto'],
                            'bajo': vela['bajo'],
                            'timestamp': vela['timestamp'],
                            'fuerza': df['volumen'].iloc[idx] / volumen_promedio.iloc[idx]
                        }
                        
                        self.estructuras_detectadas['order_blocks'].append(order_block)
            
        except Exception as e:
            logger.error(f"Error detectando order blocks: {e}")
    
    def _detectar_zonas_liquidez(self, df: pd.DataFrame):
        """
        Detecta zonas de liquidez (stops acumulados).
        
        Estas son zonas donde hay muchos stops de traders minoristas.
        """
        try:
            # Buscar máximos y mínimos recientes
            lookback = 50
            
            for i in range(lookback, len(df)):
                # Verificar si es un máximo local
                es_maximo = True
                es_minimo = True
                
                for j in range(1, 6):
                    if i - j >= 0:
                        if df['alto'].iloc[i] <= df['alto'].iloc[i - j]:
                            es_maximo = False
                        if df['bajo'].iloc[i] >= df['bajo'].iloc[i - j]:
                            es_minimo = False
                    
                    if i + j < len(df):
                        if df['alto'].iloc[i] <= df['alto'].iloc[i + j]:
                            es_maximo = False
                        if df['bajo'].iloc[i] >= df['bajo'].iloc[i + j]:
                            es_minimo = False
                
                if es_maximo:
                    zona = {
                        'tipo': 'liquidez_alcista',
                        'precio': df['alto'].iloc[i],
                        'timestamp': df['timestamp'].iloc[i],
                        'fuerza': 1.0
                    }
                    self.estructuras_detectadas['zonas_liquidez'].append(zona)
                
                if es_minimo:
                    zona = {
                        'tipo': 'liquidez_bajista',
                        'precio': df['bajo'].iloc[i],
                        'timestamp': df['timestamp'].iloc[i],
                        'fuerza': 1.0
                    }
                    self.estructuras_detectadas['zonas_liquidez'].append(zona)
            
        except Exception as e:
            logger.error(f"Error detectando zonas de liquidez: {e}")
    
    def _detectar_soportes_resistencias(self, df: pd.DataFrame):
        """
        Detecta niveles de soporte y resistencia.
        """
        try:
            # Usar pivote de Fibonacci para identificar niveles clave
            max_price = df['alto'].max()
            min_price = df['bajo'].min()
            
            niveles_fib = {
                'fib_236': min_price + (max_price - min_price) * 0.236,
                'fib_382': min_price + (max_price - min_price) * 0.382,
                'fib_500': min_price + (max_price - min_price) * 0.5,
                'fib_618': min_price + (max_price - min_price) * 0.618,
                'fib_786': min_price + (max_price - min_price) * 0.786
            }
            
            for nombre, precio in niveles_fib.items():
                # Verificar si el precio actual está cerca de este nivel
                precio_actual = df['cierre'].iloc[-1]
                distancia_pct = abs(precio_actual - precio) / precio_actual
                
                if distancia_pct < 0.01:  # Dentro del 1%
                    nivel = {
                        'tipo': 'soporte' if precio_actual > precio else 'resistencia',
                        'nivel': nombre,
                        'precio': precio,
                        'fuerza': 1.0 - distancia_pct * 100
                    }
                    self.estructuras_detectadas['soportes_resistencias'].append(nivel)
            
        except Exception as e:
            logger.error(f"Error detectando soportes/resistencias: {e}")
    
    def _determinar_tendencia(self, analisis: Dict) -> str:
        """
        Determina la tendencia general del mercado.
        
        Args:
            analisis: Análisis completo
            
        Returns:
            Tendencia general
        """
        if 'multi_tf' in analisis:
            mft = analisis['multi_tf']
            if mft['alineacion']:
                return mft['tendencia_conjunta']
        
        # Si no hay alineación, usar timeframe principal
        tf_principal = self.config['timeframes']['principal']
        if tf_principal in analisis:
            tendencia_tf = analisis[tf_principal]['tendencia']
            if 'alcista' in tendencia_tf:
                return 'alcista'
            elif 'bajista' in tendencia_tf:
                return 'bajista'
        
        return 'neutral'
    
    def generar_senales(self, analisis: Dict) -> List[Señal]:
        """
        Genera señales de trading basadas en el análisis.
        
        Args:
            analisis: Resultado del análisis
            
        Returns:
            Lista de señales generadas
        """
        senales = []
        
        try:
            # 1. Generar señales usando el generador
            senales_base = self.generador_senales.generar_senales(analisis)
            
            # 2. Aplicar filtros de la estrategia avanzada
            for senal_base in senales_base:
                senal_mejorada = self._mejorar_senal(senal_base, analisis)
                
                # Verificar estructuras de confirmación
                if self._confirmar_con_estructuras(senal_mejorada):
                    senal_mejorada.agregar_confirmacion("estructura")
                
                # Verificar volumen
                if self._confirmar_con_volumen(senal_mejorada, analisis):
                    senal_mejorada.agregar_confirmacion("volumen")
                
                # Verificar multi-timeframe
                if self._confirmar_multi_timeframe(senal_mejorada, analisis):
                    senal_mejorada.agregar_confirmacion("multi_tf")
                
                # Si la señal tiene suficientes confirmaciones, añadirla
                if len(senal_mejorada.confirmaciones) >= 2:
                    senales.append(senal_mejorada)
                    self.registrar_senal(senal_mejorada)
            
            # 3. Limitar número de señales por ciclo
            senales = senales[:self.parametros['max_senales_por_ciclo']]
            
            return senales
            
        except Exception as e:
            logger.error(f"Error generando señales: {e}")
            return []
    
    def _mejorar_senal(self, senal_base: Señal, analisis: Dict) -> Señal:
        """
        Mejora una señal base con información adicional.
        
        Args:
            senal_base: Señal base
            analisis: Análisis completo
            
        Returns:
            Señal mejorada
        """
        # Mejorar con información de estructuras
        if 'estructuras' in analisis:
            estructuras = analisis['estructuras']
            
            # Buscar order blocks cercanos
            for ob in estructuras.get('order_blocks', []):
                distancia = abs(senal_base.precio_entrada - ob['alto'])
                if distancia < (analisis.get('H1', {}).get('atr_actual', 0.001) * 2):
                    if (ob['tipo'] == 'alcista' and senal_base.direccion == 'COMPRA') or \
                       (ob['tipo'] == 'bajista' and senal_base.direccion == 'VENTA'):
                        senal_base.fuerza += 20
                        senal_base.agregar_confirmacion("order_block_cercano")
        
        return senal_base
    
    def _confirmar_con_estructuras(self, senal: Señal) -> bool:
        """
        Confirma una señal con estructuras detectadas.
        
        Args:
            senal: Señal a confirmar
            
        Returns:
            True si se confirma
        """
        if not self.estructuras_detectadas['order_blocks']:
            return False
        
        # Verificar si hay order blocks que apoyen la dirección
        for ob in self.estructuras_detectadas['order_blocks']:
            if ob['tipo'] == 'alcista' and senal.direccion == 'COMPRA':
                return True
            elif ob['tipo'] == 'bajista' and senal.direccion == 'VENTA':
                return True
        
        return False
    
    def _confirmar_con_volumen(self, senal: Señal, analisis: Dict) -> bool:
        """
        Confirma una señal con análisis de volumen.
        
        Args:
            senal: Señal a confirmar
            analisis: Análisis completo
            
        Returns:
            True si se confirma con volumen
        """
        tf_entrada = self.config['timeframes']['entrada']
        
        if tf_entrada in analisis:
            volumen_alto = analisis[tf_entrada].get('volumen_alto', False)
            return volumen_alto
        
        return False
    
    def _confirmar_multi_timeframe(self, senal: Señal, analisis: Dict) -> bool:
        """
        Confirma una señal con análisis multi-timeframe.
        
        Args:
            senal: Señal a confirmar
            analisis: Análisis completo
            
        Returns:
            True si se confirma en múltiples timeframes
        """
        if 'multi_tf' not in analisis:
            return False
        
        mft = analisis['multi_tf']
        
        if not mft['alineacion']:
            return False
        
        # Verificar que la dirección de la señal coincida con la tendencia conjunta
        if (mft['tendencia_conjunta'] == 'alcista' and senal.direccion == 'COMPRA') or \
           (mft['tendencia_conjunta'] == 'bajista' and senal.direccion == 'VENTA'):
            return True
        
        return False
    
    def obtener_resumen_analisis(self) -> Dict:
        """
        Obtiene un resumen del último análisis.
        
        Returns:
            Diccionario con resumen
        """
        if not self.ultimo_analisis:
            return {}
        
        resumen = {
            'timestamp': datetime.now().isoformat(),
            'tendencia_general': self.ultimo_analisis.get('tendencia_general', 'neutral'),
            'estructuras_detectadas': len(self.estructuras_detectadas['order_blocks']),
            'senales_generadas': len(self.historial_senales)
        }
        
        return resumen