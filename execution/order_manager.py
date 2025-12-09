"""
Gestor de órdenes con protección contra duplicados y gestión de latencia.
"""
import time
import threading
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

from core.exceptions import ErrorOrden
from execution.broker import Broker, ResultadoOrden

class OrderManager:
    """Gestiona la ejecución de órdenes con protección y reintentos."""
    
    def __init__(self, broker: Broker, config):
        """Inicializa el gestor de órdenes."""
        self.broker = broker
        self.config = config
        self.ordenes_recientes = defaultdict(list)
        self.bloqueos_simbolo = {}
        self.lock = threading.Lock()
        
        # Configuración
        self.tiempo_minimo_entre_ordenes = 30  # segundos
        self.max_ordenes_por_simbolo = 1  # máximo de órdenes abiertas por símbolo
        self.max_reintentos = 3
        
    def colocar_orden_con_proteccion(self, orden_dict: Dict) -> ResultadoOrden:
        """
        Coloca una orden con protección contra duplicados y validaciones.
        
        Args:
            orden_dict: Diccionario con datos de la orden
            
        Returns:
            Resultado de la operación
        """
        try:
            with self.lock:
                simbolo = orden_dict.get('simbolo')
                tipo = orden_dict.get('tipo')
                
                # 1. Validar símbolo no bloqueado
                if self._simbolo_bloqueado(simbolo):
                    return ResultadoOrden(
                        exito=False,
                        mensaje=f"Símbolo {simbolo} temporalmente bloqueado"
                    )
                
                # 2. Verificar orden duplicada reciente
                if self._es_orden_duplicada(simbolo, tipo, orden_dict.get('precio')):
                    return ResultadoOrden(
                        exito=False,
                        mensaje=f"Orden duplicada para {simbolo} {tipo}"
                    )
                
                # 3. Verificar límite de órdenes por símbolo
                if not self._puede_colocar_orden(simbolo):
                    return ResultadoOrden(
                        exito=False,
                        mensaje=f"Límite de órdenes alcanzado para {simbolo}"
                    )
                
                # 4. Colocar orden con reintentos
                resultado = self._colocar_orden_con_reintentos(orden_dict)
                
                # 5. Registrar orden si fue exitosa
                if resultado.exito:
                    self._registrar_orden_reciente(simbolo, tipo, resultado.precio)
                    
                    # Bloquear símbolo temporalmente si hubo error
                    if not resultado.exito and "Error" in resultado.mensaje:
                        self._bloquear_simbolo(simbolo, 60)  # Bloquear por 60 segundos
                
                return resultado
                
        except Exception as e:
            logger.error(f"Error en gestión de orden: {e}")
            return ResultadoOrden(
                exito=False,
                mensaje=f"Error en gestión de orden: {str(e)}"
            )
    
    def _colocar_orden_con_reintentos(self, orden_dict: Dict) -> ResultadoOrden:
        """Coloca una orden con reintentos en caso de fallo."""
        ultimo_error = None
        
        for intento in range(self.max_reintentos):
            try:
                # Convertir diccionario a objeto Orden
                from execution.broker import Orden
                orden = Orden(**orden_dict)
                
                # Colocar orden
                resultado = self.broker.colocar_orden(orden)
                
                if resultado.exito:
                    logger.info(f"Orden colocada exitosamente en intento {intento + 1}")
                    return resultado
                else:
                    ultimo_error = resultado.mensaje
                    logger.warning(f"Intento {intento + 1} fallido: {resultado.mensaje}")
                    
                    if intento < self.max_reintentos - 1:
                        tiempo_espera = (intento + 1) * 2  # Espera exponencial
                        time.sleep(tiempo_espera)
            
            except Exception as e:
                ultimo_error = str(e)
                logger.error(f"Error en intento {intento + 1}: {e}")
                
                if intento < self.max_reintentos - 1:
                    time.sleep((intento + 1) * 2)
        
        return ResultadoOrden(
            exito=False,
            mensaje=f"Todos los intentos fallaron. Último error: {ultimo_error}"
        )
    
    def _es_orden_duplicada(self, simbolo: str, tipo: str, precio: float) -> bool:
        """Verifica si una orden es duplicada de una reciente."""
        if simbolo not in self.ordenes_recientes:
            return False
        
        ahora = datetime.now()
        margen_precio = 0.0001  # 1 pip
        
        for orden in self.ordenes_recientes[simbolo]:
            # Verificar tiempo (últimos 30 segundos)
            tiempo_transcurrido = (ahora - orden['timestamp']).total_seconds()
            
            if tiempo_transcurrido < self.tiempo_minimo_entre_ordenes:
                # Verificar si es la misma dirección y precio similar
                if (orden['tipo'] == tipo and 
                    abs(orden['precio'] - precio) < margen_precio):
                    return True
        
        return False
    
    def _puede_colocar_orden(self, simbolo: str) -> bool:
        """Verifica si se puede colocar una nueva orden para el símbolo."""
        # Obtener posiciones abiertas para este símbolo
        posiciones = self.broker.obtener_posiciones_abiertas()
        posiciones_simbolo = [p for p in posiciones if p['simbolo'] == simbolo]
        
        return len(posiciones_simbolo) < self.max_ordenes_por_simbolo
    
    def _simbolo_bloqueado(self, simbolo: str) -> bool:
        """Verifica si un símbolo está temporalmente bloqueado."""
        if simbolo in self.bloqueos_simbolo:
            tiempo_bloqueo = self.bloqueos_simbolo[simbolo]
            if datetime.now() < tiempo_bloqueo:
                return True
            else:
                # Eliminar bloqueo expirado
                del self.bloqueos_simbolo[simbolo]
        
        return False
    
    def _bloquear_simbolo(self, simbolo: str, segundos: int):
        """Bloquea un símbolo temporalmente."""
        tiempo_desbloqueo = datetime.now() + timedelta(seconds=segundos)
        self.bloqueos_simbolo[simbolo] = tiempo_desbloqueo
        logger.warning(f"Símbolo {simbolo} bloqueado por {segundos} segundos")
    
    def _registrar_orden_reciente(self, simbolo: str, tipo: str, precio: float):
        """Registra una orden recientemente colocada."""
        registro = {
            'simbolo': simbolo,
            'tipo': tipo,
            'precio': precio,
            'timestamp': datetime.now()
        }
        
        self.ordenes_recientes[simbolo].append(registro)
        
        # Mantener solo las órdenes de los últimos 5 minutos
        cutoff_time = datetime.now() - timedelta(minutes=5)
        self.ordenes_recientes[simbolo] = [
            o for o in self.ordenes_recientes[simbolo]
            if o['timestamp'] > cutoff_time
        ]
    
    def limpiar_ordenes_antiguas(self):
        """Limpia registros de órdenes antiguas."""
        cutoff_time = datetime.now() - timedelta(minutes=10)
        
        for simbolo in list(self.ordenes_recientes.keys()):
            self.ordenes_recientes[simbolo] = [
                o for o in self.ordenes_recientes[simbolo]
                if o['timestamp'] > cutoff_time
            ]
            
            # Eliminar símbolos sin órdenes recientes
            if not self.ordenes_recientes[simbolo]:
                del self.ordenes_recientes[simbolo]
    
    def gestionar_ordenes_abiertas(self):
        """Gestiona órdenes abiertas (trailing stop, break even, etc.)."""
        try:
            posiciones = self.broker.obtener_posiciones_abiertas()
            
            for posicion in posiciones:
                self._aplicar_trailing_stop(posicion)
                self._aplicar_break_even(posicion)
                self._verificar_stop_loss_take_profit(posicion)
                
        except Exception as e:
            logger.error(f"Error gestionando órdenes abiertas: {e}")
    
    def _aplicar_trailing_stop(self, posicion: Dict):
        """Aplica trailing stop a una posición."""
        if not self.config['riesgo']['trailing_stop']['habilitado']:
            return
        
        try:
            activacion_pips = self.config['riesgo']['trailing_stop']['activacion_pips']
            paso_pips = self.config['riesgo']['trailing_stop']['paso_pips']
            
            precio_apertura = posicion['precio_apertura']
            precio_actual = posicion['precio_actual']
            stop_loss_actual = posicion['stop_loss']
            
            if stop_loss_actual is None:
                return
            
            # Calcular beneficio en pips
            if posicion['tipo'] == 'COMPRA':
                beneficio_pips = (precio_actual - precio_apertura) * 10000
                if beneficio_pips >= activacion_pips:
                    nuevo_sl = precio_actual - (paso_pips / 10000)
                    if nuevo_sl > stop_loss_actual:
                        self.broker.modificar_orden(posicion['ticket'], {'stop_loss': nuevo_sl})
                        
            elif posicion['tipo'] == 'VENTA':
                beneficio_pips = (precio_apertura - precio_actual) * 10000
                if beneficio_pips >= activacion_pips:
                    nuevo_sl = precio_actual + (paso_pips / 10000)
                    if nuevo_sl < stop_loss_actual:
                        self.broker.modificar_orden(posicion['ticket'], {'stop_loss': nuevo_sl})
                        
        except Exception as e:
            logger.error(f"Error aplicando trailing stop: {e}")
    
    def _aplicar_break_even(self, posicion: Dict):
        """Aplica break even a una posición."""
        if not self.config['riesgo']['break_even']['habilitado']:
            return
        
        try:
            activacion_pips = self.config['riesgo']['break_even']['activacion_pips']
            
            precio_apertura = posicion['precio_apertura']
            precio_actual = posicion['precio_actual']
            stop_loss_actual = posicion['stop_loss']
            
            if stop_loss_actual is None:
                return
            
            # Calcular beneficio en pips
            if posicion['tipo'] == 'COMPRA':
                beneficio_pips = (precio_actual - precio_apertura) * 10000
                if beneficio_pips >= activacion_pips:
                    # Mover SL a break even (precio apertura + spread)
                    nuevo_sl = precio_apertura + 0.0001  # 1 pip sobre apertura
                    if nuevo_sl > stop_loss_actual:
                        self.broker.modificar_orden(posicion['ticket'], {'stop_loss': nuevo_sl})
                        
            elif posicion['tipo'] == 'VENTA':
                beneficio_pips = (precio_apertura - precio_actual) * 10000
                if beneficio_pips >= activacion_pips:
                    nuevo_sl = precio_apertura - 0.0001  # 1 pip bajo apertura
                    if nuevo_sl < stop_loss_actual:
                        self.broker.modificar_orden(posicion['ticket'], {'stop_loss': nuevo_sl})
                        
        except Exception as e:
            logger.error(f"Error aplicando break even: {e}")
    
    def _verificar_stop_loss_take_profit(self, posicion: Dict):
        """Verifica si se alcanzó SL o TP."""
        # Esta verificación se hace automáticamente en MT5
        # En modo simulado, se podría implementar lógica adicional
        pass