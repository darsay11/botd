"""
Motor de backtesting tick-by-tick.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from tqdm import tqdm
from loguru import logger

from data.tick_simulator import TickSimulator
from strategies.advanced_strategy import AdvancedStrategy
from execution.broker import BrokerSimulado
from risk.risk_manager import RiskManager
from backtest.reporter import BacktestReporter

class BacktestEngine:
    """Motor de backtesting con simulación tick-by-tick."""
    
    def __init__(self, config):
        """Inicializa el motor de backtesting."""
        self.config = config
        self.capital_inicial = config['backtesting']['capital_inicial']
        self.fecha_inicio = datetime.strptime(config['backtesting']['fecha_inicio'], '%Y-%m-%d')
        self.fecha_fin = datetime.strptime(config['backtesting']['fecha_fin'], '%Y-%m-%d')
        
        # Inicializar componentes
        self.estrategia = AdvancedStrategy(config)
        self.broker = BrokerSimulado(config)
        self.gestor_riesgo = RiskManager(config)
        self.simulador = None
        self.reporter = BacktestReporter()
        
        # Resultados
        self.resultados = {
            'operaciones': [],
            'metricas': {},
            'equity_curve': [],
            'drawdowns': []
        }
        
        logger.info(f"Motor de backtesting inicializado: {self.fecha_inicio} - {self.fecha_fin}")
    
    def cargar_datos(self, datos_velas: Dict[str, pd.DataFrame]):
        """
        Carga datos para backtesting.
        
        Args:
            datos_velas: Diccionario con DataFrames por timeframe
        """
        try:
            # Usar timeframe de entrada para simulación de ticks
            tf_entrada = self.config['timeframes']['entrada']
            
            if tf_entrada not in datos_velas:
                raise ValueError(f"Timeframe de entrada '{tf_entrada}' no encontrado en datos")
            
            df_entrada = datos_velas[tf_entrada]
            
            # Filtrar por rango de fechas
            mask = (df_entrada['timestamp'] >= self.fecha_inicio) & (df_entrada['timestamp'] <= self.fecha_fin)
            df_filtrado = df_entrada[mask].copy()
            
            if len(df_filtrado) == 0:
                raise ValueError(f"No hay datos en el rango {self.fecha_inicio} - {self.fecha_fin}")
            
            # Crear simulador de ticks
            spread = self.config['backtesting']['spread_promedio'] / 10000
            self.simulador = TickSimulator(df_filtrado, spread)
            
            # Guardar datos para análisis multi-timeframe
            self.datos_multi_tf = {}
            for tf, df in datos_velas.items():
                mask = (df['timestamp'] >= self.fecha_inicio) & (df['timestamp'] <= self.fecha_fin)
                self.datos_multi_tf[tf] = df[mask].copy()
            
            logger.info(f"Datos cargados: {len(df_filtrado)} velas, {tf_entrada} timeframe")
            
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            raise
    
    def ejecutar(self) -> Dict:
        """
        Ejecuta el backtesting completo.
        
        Returns:
            Diccionario con resultados
        """
        try:
            logger.info("Iniciando backtesting...")
            
            # Resetear componentes
            self.simulador.reset()
            self.estrategia.reset()
            
            # Variables de control
            tick_count = 0
            operaciones_count = 0
            ultima_actualizacion_analisis = None
            
            # Barra de progreso
            with tqdm(desc="Backtesting", unit="ticks") as pbar:
                while True:
                    # Obtener siguiente tick
                    tick = self.simulador.obtener_siguiente_tick()
                    if tick is None:
                        break
                    
                    tick_count += 1
                    
                    # Actualizar precios en posiciones abiertas
                    self._actualizar_precios_posiciones(tick)
                    
                    # Ejecutar análisis cada N ticks o cada cierto tiempo
                    if (ultima_actualizacion_analisis is None or 
                        tick['timestamp'] - ultima_actualizacion_analisis > timedelta(minutes=5)):
                        
                        # Obtener datos actualizados para análisis
                        datos_actuales = self._obtener_datos_actualizados(tick['timestamp'])
                        
                        if datos_actuales:
                            # Ejecutar análisis
                            analisis = self.estrategia.analizar_mercado(datos_actuales)
                            senales = self.estrategia.generar_senales(analisis)
                            
                            # Procesar señales
                            for senal in senales:
                                if self.gestor_riesgo.validar_senal(senal):
                                    # Preparar y colocar orden
                                    orden = self.gestor_riesgo.preparar_orden(senal)
                                    resultado = self.broker.colocar_orden(orden)
                                    
                                    if resultado.exito:
                                        operaciones_count += 1
                                        logger.debug(f"Operación #{operaciones_count} colocada")
                            
                            ultima_actualizacion_analisis = tick['timestamp']
                    
                    # Gestionar órdenes abiertas (trailing stop, etc.)
                    self._gestionar_ordenes_abiertas()
                    
                    # Registrar punto en curva de equity
                    if tick_count % 100 == 0:  # Cada 100 ticks
                        self._registrar_punto_equity(tick['timestamp'])
                    
                    # Actualizar barra de progreso
                    pbar.update(1)
                    pbar.set_postfix({
                        'ticks': tick_count,
                        'ops': operaciones_count,
                        'equity': f"${self.broker.equity:.2f}"
                    })
            
            # Finalizar backtesting
            self._finalizar_backtest()
            
            logger.info(f"Backtesting completado: {tick_count} ticks, {operaciones_count} operaciones")
            
            return self.resultados
            
        except Exception as e:
            logger.error(f"Error en backtesting: {e}")
            raise
    
    def _actualizar_precios_posiciones(self, tick: Dict):
        """Actualiza precios en posiciones abiertas."""
        posiciones = self.broker.obtener_posiciones_abiertas()
        
        for posicion in posiciones:
            if posicion['simbolo'] == tick.get('simbolo'):
                # Actualizar precio actual
                posicion['precio_actual'] = tick['last']
                
                # Verificar stop loss y take profit
                self._verificar_sl_tp(posicion, tick)
    
    def _verificar_sl_tp(self, posicion: Dict, tick: Dict):
        """Verifica si se alcanzó SL o TP."""
        precio_actual = tick['last']
        stop_loss = posicion.get('stop_loss')
        take_profit = posicion.get('take_profit')
        
        if stop_loss is None or take_profit is None:
            return
        
        ticket = posicion['ticket']
        
        if posicion['tipo'] == 'COMPRA':
            if precio_actual <= stop_loss:
                self.broker.cerrar_orden(ticket)
                logger.debug(f"SL alcanzado para posición {ticket}")
            elif precio_actual >= take_profit:
                self.broker.cerrar_orden(ticket)
                logger.debug(f"TP alcanzado para posición {ticket}")
        else:  # VENTA
            if precio_actual >= stop_loss:
                self.broker.cerrar_orden(ticket)
                logger.debug(f"SL alcanzado para posición {ticket}")
            elif precio_actual <= take_profit:
                self.broker.cerrar_orden(ticket)
                logger.debug(f"TP alcanzado para posición {ticket}")
    
    def _obtener_datos_actualizados(self, timestamp: datetime) -> Dict:
        """Obtiene datos actualizados para análisis."""
        datos = {}
        
        for tf, df in self.datos_multi_tf.items():
            # Filtrar datos hasta el timestamp actual
            df_filtrado = df[df['timestamp'] <= timestamp].copy()
            
            if len(df_filtrado) > 0:
                # Tomar las últimas N velas
                n_velas = 500  # Cantidad de velas para análisis
                datos[tf] = df_filtrado.tail(min(n_velas, len(df_filtrado)))
        
        return datos
    
    def _gestionar_ordenes_abiertas(self):
        """Gestiona órdenes abiertas."""
        # En backtesting simple, la gestión se hace en _verificar_sl_tp
        # Se podría añadir lógica de trailing stop aquí
        pass
    
    def _registrar_punto_equity(self, timestamp: datetime):
        """Registra un punto en la curva de equity."""
        estado_cuenta = self.broker.obtener_estado_cuenta()
        
        self.resultados['equity_curve'].append({
            'timestamp': timestamp,
            'equity': estado_cuenta.get('equity', 0),
            'balance': estado_cuenta.get('balance', 0)
        })
    
    def _finalizar_backtest(self):
        """Finaliza el backtesting y calcula resultados."""
        # Cerrar todas las posiciones abiertas
        self.broker.cerrar()
        
        # Obtener historial de operaciones
        historial = self.broker.obtener_historial()
        self.resultados['operaciones'] = historial
        
        # Calcular métricas
        self._calcular_metricas()
        
        # Generar reporte
        self.reporter.generar_reporte(self.resultados, self.config)
    
    def _calcular_metricas(self):
        """Calcula métricas de rendimiento."""
        try:
            operaciones = self.resultados['operaciones']
            
            if not operaciones:
                self.resultados['metricas'] = {
                    'total_operaciones': 0,
                    'operaciones_ganadoras': 0,
                    'operaciones_perdedoras': 0,
                    'win_rate': 0,
                    'beneficio_total': 0,
                    'drawdown_maximo': 0,
                    'sharpe_ratio': 0,
                    'expectancy': 0
                }
                return
            
            # Métricas básicas
            total_operaciones = len(operaciones)
            operaciones_ganadoras = [op for op in operaciones if op['beneficio'] > 0]
            operaciones_perdedoras = [op for op in operaciones if op['beneficio'] < 0]
            
            win_rate = len(operaciones_ganadoras) / total_operaciones * 100
            
            # Beneficio total
            beneficio_total = sum(op['beneficio'] for op in operaciones)
            
            # Drawdown máximo
            equity_series = pd.Series([p['equity'] for p in self.resultados['equity_curve']])
            rolling_max = equity_series.expanding().max()
            drawdowns = (equity_series - rolling_max) / rolling_max * 100
            drawdown_maximo = abs(drawdowns.min()) if len(drawdowns) > 0 else 0
            
            # Sharpe ratio (simplificado)
            if len(self.resultados['equity_curve']) > 1:
                returns = pd.Series([p['equity'] for p in self.resultados['equity_curve']]).pct_change().dropna()
                if returns.std() > 0:
                    sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
                else:
                    sharpe_ratio = 0
            else:
                sharpe_ratio = 0
            
            # Expectancy
            if operaciones_ganadoras and operaciones_perdedoras:
                avg_ganancia = np.mean([op['beneficio'] for op in operaciones_ganadoras])
                avg_perdida = abs(np.mean([op['beneficio'] for op in operaciones_perdedoras]))
                probabilidad_ganar = len(operaciones_ganadoras) / total_operaciones
                expectancy = (probabilidad_ganar * avg_ganancia) - ((1 - probabilidad_ganar) * avg_perdida)
            else:
                expectancy = 0
            
            self.resultados['metricas'] = {
                'total_operaciones': total_operaciones,
                'operaciones_ganadoras': len(operaciones_ganadoras),
                'operaciones_perdedoras': len(operaciones_perdedoras),
                'win_rate': win_rate,
                'beneficio_total': beneficio_total,
                'drawdown_maximo': drawdown_maximo,
                'sharpe_ratio': sharpe_ratio,
                'expectancy': expectancy,
                'retorno_total': (beneficio_total / self.capital_inicial) * 100,
                'retorno_anualizado': (beneficio_total / self.capital_inicial) * 100 * (252 / len(operaciones)) if operaciones else 0
            }
            
            # Calcular drawdowns individuales
            self.resultados['drawdowns'] = drawdowns.tolist()
            
        except Exception as e:
            logger.error(f"Error calculando métricas: {e}")
            self.resultados['metricas'] = {}
    
    def optimizar_parametros(self, parametros_grid: Dict) -> List[Dict]:
        """
        Optimiza parámetros usando grid search.
        
        Args:
            parametros_grid: Diccionario con rangos de parámetros
            
        Returns:
            Lista de resultados de optimización
        """
        resultados_optimizacion = []
        
        try:
            logger.info("Iniciando optimización de parámetros...")
            
            # Ejemplo: optimizar EMAs y RSI
            if 'ema_rapida' in parametros_grid and 'ema_lenta' in parametros_grid:
                emas_rapidas = parametros_grid['ema_rapida']
                emas_lentas = parametros_grid['ema_lenta']
                
                total_combinaciones = len(emas_rapidas) * len(emas_lentas)
                combinacion_actual = 0
                
                for ema_rapida in emas_rapidas:
                    for ema_lenta in emas_lentas:
                        if ema_lenta <= ema_rapida:
                            continue  # EMA lenta debe ser mayor que rápida
                        
                        combinacion_actual += 1
                        logger.info(f"Probando combinación {combinacion_actual}/{total_combinaciones}: "
                                  f"EMA {ema_rapida}/{ema_lenta}")
                        
                        # Actualizar configuración
                        config_temp = self.config.config.copy()
                        config_temp['indicadores']['ema_rapida'] = ema_rapida
                        config_temp['indicadores']['ema_lenta'] = ema_lenta
                        
                        # Crear nueva estrategia con parámetros actualizados
                        from strategies.advanced_strategy import AdvancedStrategy
                        estrategia_temp = AdvancedStrategy(config_temp)
                        
                        # Ejecutar backtesting rápido
                        resultados = self._ejecutar_backtest_rapido(estrategia_temp)
                        
                        # Guardar resultados
                        resultados_optimizacion.append({
                            'parametros': {
                                'ema_rapida': ema_rapida,
                                'ema_lenta': ema_lenta
                            },
                            'metricas': resultados['metricas']
                        })
            
            # Ordenar por beneficio total
            resultados_optimizacion.sort(key=lambda x: x['metricas'].get('beneficio_total', 0), reverse=True)
            
            logger.info(f"Optimización completada: {len(resultados_optimizacion)} combinaciones probadas")
            
            return resultados_optimizacion
            
        except Exception as e:
            logger.error(f"Error en optimización: {e}")
            return []
    
    def _ejecutar_backtest_rapido(self, estrategia) -> Dict:
        """Ejecuta un backtesting rápido para optimización."""
        # Implementación simplificada para optimización
        # En producción, se podría reutilizar la lógica principal con muestreo reducido
        return {'metricas': {}}