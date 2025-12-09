"""
Gestor de riesgo profesional para trading.
"""
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger

from core.exceptions import ErrorRiesgo
from execution.broker import Orden

class RiskManager:
    """Gestiona el riesgo de las operaciones de trading."""
    
    def __init__(self, config):
        """Inicializa el gestor de riesgo."""
        self.config = config
        self.capital = config['backtesting']['capital_inicial']
        self.riesgo_por_operacion = config['riesgo']['porcentaje_por_operacion'] / 100
        self.riesgo_maximo_diario = config['riesgo']['riesgo_maximo_diario'] / 100
        self.riesgo_acumulado_hoy = 0.0
        self.operaciones_hoy = 0
        self.max_operaciones_diarias = 10
        self.ultimo_reinicio = datetime.now().date()
        
        logger.info("Gestor de riesgo inicializado")
    
    def validar_senal(self, senal: Dict) -> bool:
        """
        Valida si una señal cumple con los criterios de riesgo.
        
        Args:
            senal: Señal a validar
            
        Returns:
            True si la señal es válida
        """
        try:
            # 1. Verificar reinicio diario
            self._verificar_reinicio_diario()
            
            # 2. Verificar límite de operaciones diarias
            if self.operaciones_hoy >= self.max_operaciones_diarias:
                logger.warning(f"Límite de operaciones diarias alcanzado: {self.operaciones_hoy}")
                return False
            
            # 3. Verificar riesgo máximo diario
            if self.riesgo_acumulado_hoy >= self.riesgo_maximo_diario:
                logger.warning(f"Riesgo diario máximo alcanzado: {self.riesgo_acumulado_hoy*100:.1f}%")
                return False
            
            # 4. Verificar fuerza mínima de señal
            if senal.get('fuerza', 0) < 50:
                logger.warning(f"Señal con fuerza insuficiente: {senal.get('fuerza', 0)}")
                return False
            
            # 5. Verificar confirmaciones mínimas
            if len(senal.get('confirmaciones', [])) < 2:
                logger.warning(f"Señal con confirmaciones insuficientes: {senal.get('confirmaciones', [])}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando señal: {e}")
            return False
    
    def preparar_orden(self, senal: Dict) -> Orden:
        """
        Prepara una orden con parámetros de riesgo calculados.
        
        Args:
            senal: Señal de entrada
            
        Returns:
            Orden preparada
        """
        try:
            # 1. Calcular tamaño de posición
            volumen = self._calcular_volumen(senal)
            
            # 2. Calcular stop loss
            stop_loss = self._calcular_stop_loss(senal)
            
            # 3. Calcular take profit
            take_profit = self._calcular_take_profit(senal, stop_loss)
            
            # 4. Crear orden
            orden = Orden(
                simbolo=senal['simbolo'],
                tipo=senal['direccion'],
                volumen=volumen,
                precio=senal['precio_entrada'],
                stop_loss=stop_loss,
                take_profit=take_profit,
                comentario=f"Señal: {senal.get('razon_entrada', '')}",
                magic=234000,
                desviacion=10
            )
            
            # 5. Actualizar métricas de riesgo
            self._actualizar_riesgo_acumulado(senal, stop_loss)
            
            logger.info(f"Orden preparada: {senal['direccion']} {senal['simbolo']} "
                       f"Vol: {volumen:.2f} SL: {stop_loss:.5f} TP: {take_profit:.5f}")
            
            return orden
            
        except Exception as e:
            logger.error(f"Error preparando orden: {e}")
            raise ErrorRiesgo(f"Error preparando orden: {e}")
    
    def _calcular_volumen(self, senal: Dict) -> float:
        """
        Calcula el volumen de la posición basado en el riesgo.
        
        Args:
            senal: Señal de entrada
            
        Returns:
            Volumen calculado
        """
        try:
            # Calcular riesgo por operación en dinero
            riesgo_dinero = self.capital * self.riesgo_por_operacion
            
            # Calcular distancia al stop loss en pips
            precio_entrada = senal['precio_entrada']
            stop_loss = self._calcular_stop_loss(senal)
            
            if stop_loss is None:
                # Usar stop loss fijo si no se puede calcular
                stop_loss_config = self.config['riesgo']['stop_loss']
                if stop_loss_config['tipo'] == 'fijo':
                    distancia_pips = stop_loss_config['puntos_fijo']
                else:
                    distancia_pips = 20  # Valor por defecto
                
                distancia_precio = distancia_pips / 10000
            else:
                distancia_precio = abs(precio_entrada - stop_loss)
            
            # Calcular valor por pip (para Forex, 1 lote = $10 por pip)
            valor_por_pip_por_lote = 10  # Para pares mayores
            
            # Calcular volumen
            volumen = riesgo_dinero / (distancia_precio * 10000 * valor_por_pip_por_lote)
            
            # Ajustar a límites del broker
            volumen_minimo = self.config['general']['lotaje_minimo']
            volumen = max(volumen_minimo, volumen)
            volumen = round(volumen, 2)  # Redondear a 2 decimales
            
            # Verificar que no exceda el margen disponible
            # (implementación simplificada)
            
            return volumen
            
        except Exception as e:
            logger.error(f"Error calculando volumen: {e}")
            # Volumen por defecto seguro
            return self.config['general']['lotaje_minimo']
    
    def _calcular_stop_loss(self, senal: Dict) -> Optional[float]:
        """
        Calcula el nivel de stop loss.
        
        Args:
            senal: Señal de entrada
            
        Returns:
            Precio de stop loss
        """
        try:
            config_sl = self.config['riesgo']['stop_loss']
            precio_entrada = senal['precio_entrada']
            atr = senal.get('metadata', {}).get('atr', 0.001)
            
            if config_sl['tipo'] == 'atr':
                # Stop loss basado en ATR
                distancia = atr * config_sl['multiplicador_atr']
                
                if senal['direccion'] == 'COMPRA':
                    return precio_entrada - distancia
                else:  # VENTA
                    return precio_entrada + distancia
                    
            elif config_sl['tipo'] == 'fijo':
                # Stop loss fijo en pips
                distancia = config_sl['puntos_fijo'] / 10000
                
                if senal['direccion'] == 'COMPRA':
                    return precio_entrada - distancia
                else:  # VENTA
                    return precio_entrada + distancia
                    
            elif config_sl['tipo'] == 'porcentaje':
                # Stop loss como porcentaje del precio
                porcentaje = config_sl['porcentaje'] / 100
                distancia = precio_entrada * porcentaje
                
                if senal['direccion'] == 'COMPRA':
                    return precio_entrada - distancia
                else:  # VENTA
                    return precio_entrada + distancia
            
            # Si no se especifica tipo, usar estructura si está disponible
            if 'estructuras' in senal.get('metadata', {}):
                estructuras = senal['metadata']['estructuras']
                # Buscar soporte/resistencia cercano
                # (implementación simplificada)
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculando stop loss: {e}")
            return None
    
    def _calcular_take_profit(self, senal: Dict, stop_loss: Optional[float]) -> Optional[float]:
        """
        Calcula el nivel de take profit.
        
        Args:
            senal: Señal de entrada
            stop_loss: Nivel de stop loss
            
        Returns:
            Precio de take profit
        """
        try:
            config_tp = self.config['riesgo']['take_profit']
            precio_entrada = senal['precio_entrada']
            
            if stop_loss is None:
                # Si no hay stop loss, no calcular take profit
                return None
            
            if config_tp['tipo'] == 'rr':
                # Take profit basado en ratio riesgo/recompensa
                ratio = config_tp['ratio_riesgo_recompensa']
                distancia_sl = abs(precio_entrada - stop_loss)
                
                if senal['direccion'] == 'COMPRA':
                    return precio_entrada + (distancia_sl * ratio)
                else:  # VENTA
                    return precio_entrada - (distancia_sl * ratio)
                    
            elif config_tp['tipo'] == 'fijo':
                # Take profit fijo en pips
                distancia = config_tp['puntos_fijo'] / 10000
                
                if senal['direccion'] == 'COMPRA':
                    return precio_entrada + distancia
                else:  # VENTA
                    return precio_entrada - distancia
                    
            elif config_tp['tipo'] == 'porcentaje':
                # Take profit como porcentaje del precio
                porcentaje = config_tp['porcentaje'] / 100
                distancia = precio_entrada * porcentaje
                
                if senal['direccion'] == 'COMPRA':
                    return precio_entrada + distancia
                else:  # VENTA
                    return precio_entrada - distancia
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculando take profit: {e}")
            return None
    
    def _actualizar_riesgo_acumulado(self, senal: Dict, stop_loss: Optional[float]):
        """
        Actualiza el riesgo acumulado del día.
        
        Args:
            senal: Señal de entrada
            stop_loss: Nivel de stop loss
        """
        if stop_loss is None:
            return
        
        # Calcular riesgo de esta operación
        precio_entrada = senal['precio_entrada']
        distancia = abs(precio_entrada - stop_loss)
        riesgo_operacion = distancia / precio_entrada  # Riesgo como porcentaje del precio
        
        # Actualizar métricas
        self.riesgo_acumulado_hoy += riesgo_operacion
        self.operaciones_hoy += 1
        
        logger.info(f"Riesgo actualizado: Operación {self.operaciones_hoy}, "
                   f"Riesgo acumulado: {self.riesgo_acumulado_hoy*100:.2f}%")
    
    def _verificar_reinicio_diario(self):
        """Reinicia las métricas diarias si es un nuevo día."""
        hoy = datetime.now().date()
        
        if hoy != self.ultimo_reinicio:
            self.riesgo_acumulado_hoy = 0.0
            self.operaciones_hoy = 0
            self.ultimo_reinicio = hoy
            logger.info("Métricas de riesgo reiniciadas para el nuevo día")
    
    def obtener_metricas_riesgo(self) -> Dict:
        """
        Obtiene métricas actuales de riesgo.
        
        Returns:
            Diccionario con métricas
        """
        return {
            'capital': self.capital,
            'riesgo_por_operacion': self.riesgo_por_operacion * 100,
            'riesgo_acumulado_hoy': self.riesgo_acumulado_hoy * 100,
            'riesgo_maximo_diario': self.riesgo_maximo_diario * 100,
            'operaciones_hoy': self.operaciones_hoy,
            'max_operaciones_diarias': self.max_operaciones_diarias,
            'ultimo_reinicio': self.ultimo_reinicio.isoformat()
        }
    
    def actualizar_capital(self, nuevo_capital: float):
        """
        Actualiza el capital disponible.
        
        Args:
            nuevo_capital: Nuevo valor de capital
        """
        self.capital = nuevo_capital
        logger.info(f"Capital actualizado: ${nuevo_capital:.2f}")