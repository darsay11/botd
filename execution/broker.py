"""
Módulo de ejecución de órdenes con MT5.
"""
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from loguru import logger

import MetaTrader5 as mt5

from core.exceptions import ErrorOrden, ErrorConexionMT5

@dataclass
class ResultadoOrden:
    """Resultado de una operación de orden."""
    exito: bool
    ticket: Optional[int] = None
    precio: Optional[float] = None
    volumen: Optional[float] = None
    mensaje: str = ""
    timestamp: Optional[datetime] = None
    
    def __str__(self):
        if self.exito:
            return f"Orden exitosa: Ticket {self.ticket}, Precio {self.precio}, Volumen {self.volumen}"
        else:
            return f"Orden fallida: {self.mensaje}"

@dataclass
class Orden:
    """Representa una orden de trading."""
    simbolo: str
    tipo: str  # COMPRA | VENTA
    volumen: float
    precio: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comentario: str = ""
    magic: int = 234000
    desviacion: int = 10
    tipo_orden: str = "market"  # market | limit | stop
    expiracion: Optional[datetime] = None
    
    def __post_init__(self):
        # Validar volumen mínimo
        if self.volumen < 0.01:
            raise ValueError(f"Volumen {self.volumen} menor que mínimo 0.01")

class Broker:
    """Clase base abstracta para brokers."""
    
    def __init__(self, config):
        self.config = config
        self.ordenes_pendientes = []
        self.max_reintentos = 3
        
    def colocar_orden(self, orden: Orden) -> ResultadoOrden:
        """Coloca una orden en el mercado."""
        raise NotImplementedError
    
    def modificar_orden(self, ticket: int, cambios: Dict) -> ResultadoOrden:
        """Modifica una orden existente."""
        raise NotImplementedError
    
    def cerrar_orden(self, ticket: int, volumen: Optional[float] = None) -> ResultadoOrden:
        """Cierra una orden existente."""
        raise NotImplementedError
    
    def obtener_posiciones_abiertas(self) -> List[Dict]:
        """Obtiene posiciones abiertas."""
        raise NotImplementedError
    
    def obtener_ordenes_pendientes(self) -> List[Dict]:
        """Obtiene órdenes pendientes."""
        raise NotImplementedError
    
    def obtener_estado_cuenta(self) -> Dict:
        """Obtiene estado de la cuenta."""
        raise NotImplementedError
    
    @staticmethod
    def crear_broker(modo: str, config) -> 'Broker':
        """Factory method para crear brokers."""
        if modo == 'real':
            return BrokerMT5(config)
        elif modo == 'simulado':
            return BrokerSimulado(config)
        else:
            raise ValueError(f"Modo {modo} no válido. Usar 'real' o 'simulado'")

class BrokerMT5(Broker):
    """Implementación real con MetaTrader 5."""
    
    def __init__(self, config):
        super().__init__(config)
        self.conexion_activa = False
        self.conectar()
    
    def conectar(self) -> bool:
        """Establece conexión con MT5."""
        try:
            if not mt5.initialize():
                error_msg = f"Error inicializando MT5: {mt5.last_error()}"
                logger.error(error_msg)
                raise ErrorConexionMT5(error_msg)
            
            self.conexion_activa = True
            logger.info("Conectado a MT5")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a MT5: {e}")
            raise ErrorConexionMT5(f"Error conectando a MT5: {e}")
    
    def desconectar(self):
        """Cierra conexión con MT5."""
        if self.conexion_activa:
            mt5.shutdown()
            self.conexion_activa = False
            logger.info("Desconectado de MT5")
    
    def colocar_orden(self, orden: Orden) -> ResultadoOrden:
        """Coloca una orden de mercado en MT5."""
        if not self.conexion_activa:
            return ResultadoOrden(
                exito=False,
                mensaje="No hay conexión con MT5"
            )
        
        try:
            # Determinar tipo de orden MT5
            if orden.tipo == "COMPRA":
                tipo_orden = mt5.ORDER_TYPE_BUY
                precio = mt5.symbol_info_tick(orden.simbolo).ask
            elif orden.tipo == "VENTA":
                tipo_orden = mt5.ORDER_TYPE_SELL
                precio = mt5.symbol_info_tick(orden.simbolo).bid
            else:
                return ResultadoOrden(
                    exito=False,
                    mensaje=f"Tipo de orden no válido: {orden.tipo}"
                )
            
            # Si no se especificó precio, usar el actual
            if orden.precio is None:
                orden.precio = precio
            
            # Preparar solicitud de orden
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": orden.simbolo,
                "volume": orden.volumen,
                "type": tipo_orden,
                "price": orden.precio,
                "sl": orden.stop_loss,
                "tp": orden.take_profit,
                "deviation": orden.desviacion,
                "magic": orden.magic,
                "comment": orden.comentario,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enviar orden con reintentos
            for intento in range(self.max_reintentos):
                try:
                    resultado = mt5.order_send(request)
                    
                    if resultado.retcode == mt5.TRADE_RETCODE_DONE:
                        logger.info(f"Orden colocada: Ticket {resultado.order}")
                        
                        return ResultadoOrden(
                            exito=True,
                            ticket=resultado.order,
                            precio=resultado.price,
                            volumen=resultado.volume,
                            mensaje=resultado.comment,
                            timestamp=datetime.now()
                        )
                    else:
                        logger.warning(f"Intento {intento + 1} fallido: {resultado.comment}")
                        
                        if intento < self.max_reintentos - 1:
                            time.sleep(1)  # Esperar antes de reintentar
                        else:
                            return ResultadoOrden(
                                exito=False,
                                mensaje=f"Error después de {self.max_reintentos} intentos: {resultado.comment}"
                            )
                            
                except Exception as e:
                    logger.error(f"Error en intento {intento + 1}: {e}")
                    if intento < self.max_reintentos - 1:
                        time.sleep(1)
                    else:
                        return ResultadoOrden(
                            exito=False,
                            mensaje=f"Error después de {self.max_reintentos} intentos: {str(e)}"
                        )
            
            return ResultadoOrden(
                exito=False,
                mensaje="Error desconocido al colocar orden"
            )
            
        except Exception as e:
            logger.error(f"Error colocando orden: {e}")
            return ResultadoOrden(
                exito=False,
                mensaje=f"Error colocando orden: {str(e)}"
            )
    
    def modificar_orden(self, ticket: int, cambios: Dict) -> ResultadoOrden:
        """Modifica una orden existente en MT5."""
        if not self.conexion_activa:
            return ResultadoOrden(
                exito=False,
                mensaje="No hay conexión con MT5"
            )
        
        try:
            # Verificar si la orden existe
            ordenes = mt5.orders_get(ticket=ticket)
            if not ordenes:
                return ResultadoOrden(
                    exito=False,
                    mensaje=f"Orden {ticket} no encontrada"
                )
            
            orden = ordenes[0]
            
            # Preparar solicitud de modificación
            request = {
                "action": mt5.TRADE_ACTION_MODIFY,
                "order": ticket,
                "symbol": orden.symbol,
                "volume": orden.volume_current,
                "type": orden.type,
                "price": orden.price_open,
                "sl": cambios.get('stop_loss', orden.sl),
                "tp": cambios.get('take_profit', orden.tp),
                "deviation": 10,
                "magic": orden.magic,
                "comment": cambios.get('comentario', orden.comment),
                "type_time": mt5.ORDER_TIME_GTC,
            }
            
            resultado = mt5.order_send(request)
            
            if resultado.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Orden {ticket} modificada")
                return ResultadoOrden(
                    exito=True,
                    ticket=ticket,
                    mensaje=resultado.comment,
                    timestamp=datetime.now()
                )
            else:
                logger.error(f"Error modificando orden {ticket}: {resultado.comment}")
                return ResultadoOrden(
                    exito=False,
                    mensaje=resultado.comment
                )
                
        except Exception as e:
            logger.error(f"Error modificando orden: {e}")
            return ResultadoOrden(
                exito=False,
                mensaje=f"Error modificando orden: {str(e)}"
            )
    
    def cerrar_orden(self, ticket: int, volumen: Optional[float] = None) -> ResultadoOrden:
        """Cierra una posición abierta en MT5."""
        if not self.conexion_activa:
            return ResultadoOrden(
                exito=False,
                mensaje="No hay conexión con MT5"
            )
        
        try:
            # Obtener la posición
            posiciones = mt5.positions_get(ticket=ticket)
            if not posiciones:
                return ResultadoOrden(
                    exito=False,
                    mensaje=f"Posición {ticket} no encontrada"
                )
            
            posicion = posiciones[0]
            
            # Determinar tipo de orden para cerrar
            if posicion.type == mt5.POSITION_TYPE_BUY:
                tipo_orden = mt5.ORDER_TYPE_SELL
                precio = mt5.symbol_info_tick(posicion.symbol).bid
            elif posicion.type == mt5.POSITION_TYPE_SELL:
                tipo_orden = mt5.ORDER_TYPE_BUY
                precio = mt5.symbol_info_tick(posicion.symbol).ask
            else:
                return ResultadoOrden(
                    exito=False,
                    mensaje=f"Tipo de posición no válido: {posicion.type}"
                )
            
            # Usar volumen completo si no se especifica
            if volumen is None:
                volumen = posicion.volume
            
            # Preparar solicitud de cierre
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": posicion.symbol,
                "volume": volumen,
                "type": tipo_orden,
                "position": ticket,
                "price": precio,
                "deviation": 10,
                "magic": posicion.magic,
                "comment": "Cerrado por bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            resultado = mt5.order_send(request)
            
            if resultado.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Posición {ticket} cerrada")
                return ResultadoOrden(
                    exito=True,
                    ticket=ticket,
                    precio=resultado.price,
                    volumen=resultado.volume,
                    mensaje=resultado.comment,
                    timestamp=datetime.now()
                )
            else:
                logger.error(f"Error cerrando posición {ticket}: {resultado.comment}")
                return ResultadoOrden(
                    exito=False,
                    mensaje=resultado.comment
                )
                
        except Exception as e:
            logger.error(f"Error cerrando orden: {e}")
            return ResultadoOrden(
                exito=False,
                mensaje=f"Error cerrando orden: {str(e)}"
            )
    
    def obtener_posiciones_abiertas(self) -> List[Dict]:
        """Obtiene todas las posiciones abiertas."""
        if not self.conexion_activa:
            return []
        
        try:
            posiciones = mt5.positions_get()
            
            resultado = []
            for pos in posiciones:
                resultado.append({
                    'ticket': pos.ticket,
                    'simbolo': pos.symbol,
                    'tipo': 'COMPRA' if pos.type == mt5.POSITION_TYPE_BUY else 'VENTA',
                    'volumen': pos.volume,
                    'precio_apertura': pos.price_open,
                    'precio_actual': pos.price_current,
                    'stop_loss': pos.sl,
                    'take_profit': pos.tp,
                    'beneficio': pos.profit,
                    'swap': pos.swap,
                    'comentario': pos.comment,
                    'timestamp_apertura': datetime.fromtimestamp(pos.time),
                    'magic': pos.magic
                })
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error obteniendo posiciones: {e}")
            return []
    
    def obtener_ordenes_pendientes(self) -> List[Dict]:
        """Obtiene todas las órdenes pendientes."""
        if not self.conexion_activa:
            return []
        
        try:
            ordenes = mt5.orders_get()
            
            resultado = []
            for orden in ordenes:
                resultado.append({
                    'ticket': orden.ticket,
                    'simbolo': orden.symbol,
                    'tipo': self._traducir_tipo_orden(orden.type),
                    'volumen': orden.volume_current,
                    'precio': orden.price_open,
                    'stop_loss': orden.sl,
                    'take_profit': orden.tp,
                    'comentario': orden.comment,
                    'timestamp': datetime.fromtimestamp(orden.time_setup),
                    'magic': orden.magic
                })
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error obteniendo órdenes pendientes: {e}")
            return []
    
    def obtener_estado_cuenta(self) -> Dict:
        """Obtiene información de la cuenta."""
        if not self.conexion_activa:
            return {}
        
        try:
            cuenta = mt5.account_info()
            
            if cuenta is None:
                return {}
            
            return {
                'balance': cuenta.balance,
                'equity': cuenta.equity,
                'margen': cuenta.margin,
                'margen_libre': cuenta.margin_free,
                'margen_nivel': cuenta.margin_level,
                'beneficio': cuenta.profit,
                'nombre': cuenta.name,
                'servidor': cuenta.server,
                'moneda': cuenta.currency,
                'apalancamiento': cuenta.leverage,
                'tipo': cuenta.trade_mode
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de cuenta: {e}")
            return {}
    
    def _traducir_tipo_orden(self, tipo_mt5: int) -> str:
        """Traduce tipo de orden MT5 a string."""
        tipos = {
            mt5.ORDER_TYPE_BUY: "COMPRA",
            mt5.ORDER_TYPE_SELL: "VENTA",
            mt5.ORDER_TYPE_BUY_LIMIT: "COMPRA_LIMIT",
            mt5.ORDER_TYPE_SELL_LIMIT: "VENTA_LIMIT",
            mt5.ORDER_TYPE_BUY_STOP: "COMPRA_STOP",
            mt5.ORDER_TYPE_SELL_STOP: "VENTA_STOP"
        }
        return tipos.get(tipo_mt5, "DESCONOCIDO")
    
    def cerrar(self):
        """Cierra la conexión."""
        self.desconectar()
    
    def __del__(self):
        """Destructor."""
        self.cerrar()

class BrokerSimulado(Broker):
    """Broker simulado para backtesting y pruebas."""
    
    def __init__(self, config):
        super().__init__(config)
        self.posiciones = []
        self.ordenes_pendientes = []
        self.historial = []
        self.balance = config['backtesting']['capital_inicial']
        self.equity = self.balance
        self.comision_por_lote = config['backtesting']['comision_por_lote']
        self.spread = config['backtesting']['spread_promedio'] / 10000
        
        logger.info(f"Broker simulado inicializado con balance: ${self.balance:.2f}")
    
    def colocar_orden(self, orden: Orden) -> ResultadoOrden:
        """Coloca una orden en el broker simulado."""
        try:
            # Generar ticket único
            ticket = len(self.historial) + 1000
            
            # Calcular comisión
            comision = orden.volumen * self.comision_por_lote
            
            # Para órdenes de mercado, ejecutar inmediatamente
            if orden.tipo_orden == "market":
                # Simular precio con spread
                if orden.tipo == "COMPRA":
                    precio_ejecucion = (orden.precio or 1.10000) + self.spread/2
                else:  # VENTA
                    precio_ejecucion = (orden.precio or 1.10000) - self.spread/2
                
                # Crear posición
                posicion = {
                    'ticket': ticket,
                    'simbolo': orden.simbolo,
                    'tipo': orden.tipo,
                    'volumen': orden.volumen,
                    'precio_apertura': precio_ejecucion,
                    'precio_actual': precio_ejecucion,
                    'stop_loss': orden.stop_loss,
                    'take_profit': orden.take_profit,
                    'comision': comision,
                    'swap': 0,
                    'beneficio': 0,
                    'comentario': orden.comentario,
                    'timestamp_apertura': datetime.now(),
                    'magic': orden.magic,
                    'estado': 'abierta'
                }
                
                self.posiciones.append(posicion)
                
                # Actualizar balance (restar comisión)
                self.balance -= comision
                self.equity = self.balance
                
                logger.info(f"Orden simulada: Ticket {ticket}, {orden.tipo} {orden.volumen} {orden.simbolo} @ {precio_ejecucion:.5f}")
                
                return ResultadoOrden(
                    exito=True,
                    ticket=ticket,
                    precio=precio_ejecucion,
                    volumen=orden.volumen,
                    mensaje="Orden ejecutada en simulador",
                    timestamp=datetime.now()
                )
            else:
                # Para órdenes limit/stop, añadir a pendientes
                orden_pendiente = {
                    'ticket': ticket,
                    'simbolo': orden.simbolo,
                    'tipo': orden.tipo,
                    'volumen': orden.volumen,
                    'precio': orden.precio,
                    'stop_loss': orden.stop_loss,
                    'take_profit': orden.take_profit,
                    'tipo_orden': orden.tipo_orden,
                    'comentario': orden.comentario,
                    'timestamp': datetime.now(),
                    'magic': orden.magic,
                    'estado': 'pendiente'
                }
                
                self.ordenes_pendientes.append(orden_pendiente)
                
                return ResultadoOrden(
                    exito=True,
                    ticket=ticket,
                    precio=orden.precio,
                    volumen=orden.volumen,
                    mensaje="Orden pendiente en simulador",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error en orden simulada: {e}")
            return ResultadoOrden(
                exito=False,
                mensaje=f"Error en orden simulada: {str(e)}"
            )
    
    def modificar_orden(self, ticket: int, cambios: Dict) -> ResultadoOrden:
        """Modifica una orden en el broker simulado."""
        try:
            # Buscar posición
            for posicion in self.posiciones:
                if posicion['ticket'] == ticket:
                    for key, value in cambios.items():
                        if key in posicion:
                            posicion[key] = value
                    
                    logger.info(f"Posición {ticket} modificada")
                    return ResultadoOrden(
                        exito=True,
                        ticket=ticket,
                        mensaje="Posición modificada",
                        timestamp=datetime.now()
                    )
            
            # Buscar orden pendiente
            for orden in self.ordenes_pendientes:
                if orden['ticket'] == ticket:
                    for key, value in cambios.items():
                        if key in orden:
                            orden[key] = value
                    
                    logger.info(f"Orden pendiente {ticket} modificada")
                    return ResultadoOrden(
                        exito=True,
                        ticket=ticket,
                        mensaje="Orden pendiente modificada",
                        timestamp=datetime.now()
                    )
            
            return ResultadoOrden(
                exito=False,
                mensaje=f"Orden {ticket} no encontrada"
            )
            
        except Exception as e:
            logger.error(f"Error modificando orden simulada: {e}")
            return ResultadoOrden(
                exito=False,
                mensaje=f"Error modificando orden simulada: {str(e)}"
            )
    
    def cerrar_orden(self, ticket: int, volumen: Optional[float] = None) -> ResultadoOrden:
        """Cierra una posición en el broker simulado."""
        try:
            for i, posicion in enumerate(self.posiciones):
                if posicion['ticket'] == ticket:
                    # Calcular beneficio
                    if posicion['tipo'] == "COMPRA":
                        precio_cierre = posicion['precio_actual'] - self.spread/2
                        beneficio = (precio_cierre - posicion['precio_apertura']) * posicion['volumen'] * 100000
                    else:  # VENTA
                        precio_cierre = posicion['precio_actual'] + self.spread/2
                        beneficio = (posicion['precio_apertura'] - precio_cierre) * posicion['volumen'] * 100000
                    
                    # Ajustar beneficio por comisión
                    beneficio_neto = beneficio - posicion['comision']
                    
                    # Actualizar balance
                    self.balance += beneficio_neto
                    self.equity = self.balance
                    
                    # Registrar en historial
                    operacion = posicion.copy()
                    operacion['precio_cierre'] = precio_cierre
                    operacion['beneficio'] = beneficio_neto
                    operacion['timestamp_cierre'] = datetime.now()
                    operacion['estado'] = 'cerrada'
                    self.historial.append(operacion)
                    
                    # Eliminar de posiciones abiertas
                    self.posiciones.pop(i)
                    
                    logger.info(f"Posición {ticket} cerrada: Beneficio ${beneficio_neto:.2f}")
                    
                    return ResultadoOrden(
                        exito=True,
                        ticket=ticket,
                        precio=precio_cierre,
                        volumen=posicion['volumen'],
                        mensaje=f"Posición cerrada, beneficio: ${beneficio_neto:.2f}",
                        timestamp=datetime.now()
                    )
            
            return ResultadoOrden(
                exito=False,
                mensaje=f"Posición {ticket} no encontrada"
            )
            
        except Exception as e:
            logger.error(f"Error cerrando orden simulada: {e}")
            return ResultadoOrden(
                exito=False,
                mensaje=f"Error cerrando orden simulada: {str(e)}"
            )
    
    def obtener_posiciones_abiertas(self) -> List[Dict]:
        """Obtiene posiciones abiertas en el simulador."""
        # Actualizar precios actuales y beneficios
        for posicion in self.posiciones:
            # Simular cambio de precio aleatorio pequeño
            cambio = np.random.uniform(-0.0001, 0.0001)
            posicion['precio_actual'] += cambio
            
            # Calcular beneficio actual
            if posicion['tipo'] == "COMPRA":
                beneficio = (posicion['precio_actual'] - posicion['precio_apertura']) * posicion['volumen'] * 100000
            else:  # VENTA
                beneficio = (posicion['precio_apertura'] - posicion['precio_actual']) * posicion['volumen'] * 100000
            
            posicion['beneficio'] = beneficio - posicion['comision']
        
        # Actualizar equity
        beneficio_total = sum(p['beneficio'] for p in self.posiciones)
        self.equity = self.balance + beneficio_total
        
        return self.posiciones.copy()
    
    def obtener_ordenes_pendientes(self) -> List[Dict]:
        """Obtiene órdenes pendientes en el simulador."""
        return self.ordenes_pendientes.copy()
    
    def obtener_estado_cuenta(self) -> Dict:
        """Obtiene estado de la cuenta simulada."""
        beneficio_total = sum(p['beneficio'] for p in self.posiciones)
        
        return {
            'balance': self.balance,
            'equity': self.equity,
            'margen': 0,  # No calculado en simulador simple
            'margen_libre': 0,
            'margen_nivel': 0,
            'beneficio': beneficio_total,
            'nombre': 'Cuenta Simulada',
            'servidor': 'Simulador',
            'moneda': 'USD',
            'apalancamiento': 100,
            'tipo': 0
        }
    
    def cerrar(self):
        """Cierra todas las posiciones abiertas."""
        for posicion in self.posiciones.copy():
            self.cerrar_orden(posicion['ticket'])
        
        logger.info("Broker simulado cerrado")
    
    def obtener_historial(self) -> List[Dict]:
        """Obtiene historial completo de operaciones."""
        return self.historial.copy()