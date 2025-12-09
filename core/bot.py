import MetaTrader5 as mt5
import time
from typing import Dict, Any
from loguru import logger

from configs.config_manager import ConfigManager
from core.exceptions import ErrorConexionMT5, ErrorConfiguracion

class BotTrading:
    """Clase principal del bot de trading."""
    
    def __init__(self, config_path: str = "configs/config.yml"):
        try:
            self.config = ConfigManager(config_path)
            self.conectado = False
            self.ejecutando = False
            logger.info(f"🤖 Bot inicializado - Modo: {self.config.obtener_modo_actual()}")
        except Exception as e:
            raise ErrorConfiguracion(f"Error inicializando configuración", str(e))
    
    def inicializar_modulos(self):
        """Inicializa todos los módulos del bot."""
        logger.info("🔄 Inicializando módulos del bot...")
        
        if not self.inicializar_mt5():
            raise Exception("No se pudo inicializar MT5")
        
        logger.info("✅ Módulos inicializados correctamente")
    
    def inicializar_mt5(self) -> bool:
        """Inicializa la conexión con MT5."""
        try:
            logger.info("🔌 Conectando a MT5...")
            
            mt5_config = self.config.mt5.to_dict()
            
            if not mt5.initialize(**mt5_config):
                error = mt5.last_error()
                raise ErrorConexionMT5(error[0], error[1])
            
            self.conectado = True
            
            cuenta = mt5.account_info()
            logger.info(f"✅ Conectado a MT5")
            logger.info(f"   📋 Cuenta: {cuenta.login}")
            logger.info(f"   💰 Balance: ${cuenta.balance:.2f}")
            logger.info(f"   🌐 Servidor: {cuenta.server}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a MT5: {e}")
            self.conectado = False
            return False
    
    def obtener_precios(self) -> Dict[str, Dict[str, float]]:
        """Obtiene precios actuales de los símbolos configurados."""
        if not self.conectado:
            self.inicializar_mt5()
        
        precios = {}
        for simbolo in self.config.trading.simbolos:
            try:
                seleccionado = mt5.symbol_select(simbolo, True)
                if not seleccionado:
                    continue
                
                tick = mt5.symbol_info_tick(simbolo)
                if tick:
                    spread_pips = (tick.ask - tick.bid) * 10000
                    precios[simbolo] = {
                        "bid": tick.bid,
                        "ask": tick.ask,
                        "spread": spread_pips,
                        "time": tick.time
                    }
                    hora = time.strftime("%H:%M:%S")
                    logger.info(f"[{hora}] {simbolo}: Bid={tick.bid:.5f} | Ask={tick.ask:.5f} | Spread={spread_pips:.1f}pips")
                    
            except Exception as e:
                pass
        
        return precios
    
    def iniciar(self):
        """Inicia el bot de trading."""
        logger.info("🚀 Iniciando bot de trading...")
        self.ejecutando = True
        
        try:
            contador = 0
            while self.ejecutando:
                contador += 1
                precios = self.obtener_precios()
                
                if contador % 5 == 0 and precios:
                    logger.info("─" * 60)
                
                intervalo = self.config.general.get("actualizar_intervalo", 5)
                time.sleep(intervalo)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Bot detenido por usuario")
        except Exception as e:
            logger.error(f"❌ Error en bucle principal: {e}")
        finally:
            self.detener()
    
    def detener(self):
        """Detiene el bot de trading."""
        logger.info("🛑 Deteniendo bot...")
        self.ejecutando = False
        
        if self.conectado:
            mt5.shutdown()
            self.conectado = False
            logger.info("✅ Conexión MT5 cerrada")
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Obtiene el estado actual del bot."""
        return {
            "conectado": self.conectado,
            "ejecutando": self.ejecutando,
            "modo": self.config.obtener_modo_actual(),
            "simbolos": self.config.trading.simbolos,
            "balance": mt5.account_info().balance if self.conectado else 0.0
        }
