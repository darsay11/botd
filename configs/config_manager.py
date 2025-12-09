import yaml
import os
from typing import Dict, Any, Optional

class ConfigMT5:
    """Configuración de conexión MT5."""
    def __init__(self, config_dict=None):
        config_dict = config_dict or {}
        self.path = config_dict.get('path', '')
        self.login = config_dict.get('login', 0)
        self.password = config_dict.get('password', '')
        self.server = config_dict.get('server', '')
        self.timeout = config_dict.get('timeout', 10000)
        self.portable = config_dict.get('portable', False)
    
    def to_dict(self):
        return {
            'path': self.path,
            'login': self.login,
            'password': self.password,
            'server': self.server,
            'timeout': self.timeout,
            'portable': self.portable
        }

class ConfigIndicadores:
    """Configuración de indicadores técnicos."""
    def __init__(self, config_dict=None):
        config_dict = config_dict or {}
        self.rsi_periodo = config_dict.get('rsi_periodo', 14)
        self.rsi_sobrecompra = config_dict.get('rsi_sobrecompra', 70)
        self.rsi_sobreventa = config_dict.get('rsi_sobreventa', 30)
        self.macd_fast = config_dict.get('macd_fast', 12)
        self.macd_slow = config_dict.get('macd_slow', 26)
        self.macd_signal = config_dict.get('macd_signal', 9)
        self.bb_periodo = config_dict.get('bb_periodo', 20)
        self.bb_desviacion = config_dict.get('bb_desviacion', 2.0)
    
    def to_dict(self):
        return {
            'rsi_periodo': self.rsi_periodo,
            'rsi_sobrecompra': self.rsi_sobrecompra,
            'rsi_sobreventa': self.rsi_sobreventa,
            'macd_fast': self.macd_fast,
            'macd_slow': self.macd_slow,
            'macd_signal': self.macd_signal,
            'bb_periodo': self.bb_periodo,
            'bb_desviacion': self.bb_desviacion
        }

class ConfigRiesgo:
    """Configuración de gestión de riesgo."""
    def __init__(self, config_dict=None):
        config_dict = config_dict or {}
        self.riesgo_por_operacion = config_dict.get('riesgo_por_operacion', 2.0)
        self.stop_loss_fijo_pips = config_dict.get('stop_loss_fijo_pips', 50)
        self.take_profit_fijo_pips = config_dict.get('take_profit_fijo_pips', 100)
        self.max_drawdown_diario = config_dict.get('max_drawdown_diario', 5.0)
        self.max_drawdown_total = config_dict.get('max_drawdown_total', 20.0)
        self.alerta_drawdown = config_dict.get('alerta_drawdown', 10.0)
    
    def to_dict(self):
        return {
            'riesgo_por_operacion': self.riesgo_por_operacion,
            'stop_loss_fijo_pips': self.stop_loss_fijo_pips,
            'take_profit_fijo_pips': self.take_profit_fijo_pips,
            'max_drawdown_diario': self.max_drawdown_diario,
            'max_drawdown_total': self.max_drawdown_total,
            'alerta_drawdown': self.alerta_drawdown
        }

class ConfigTrading:
    """Configuración de trading."""
    def __init__(self, config_dict=None):
        config_dict = config_dict or {}
        self.simbolos = config_dict.get('simbolos', ['EURUSD', 'GBPUSD'])
        self.timeframe = config_dict.get('timeframe', 'M15')
        self.lote_base = config_dict.get('lote_base', 0.1)
        self.lote_maximo = config_dict.get('lote_maximo', 1.0)
        self.lote_minimo = config_dict.get('lote_minimo', 0.01)
        self.max_operaciones_abiertas = config_dict.get('max_operaciones_abiertas', 3)
        self.max_operaciones_por_simbolo = config_dict.get('max_operaciones_por_simbolo', 1)
    
    def to_dict(self):
        return {
            'simbolos': self.simbolos,
            'timeframe': self.timeframe,
            'lote_base': self.lote_base,
            'lote_maximo': self.lote_maximo,
            'lote_minimo': self.lote_minimo,
            'max_operaciones_abiertas': self.max_operaciones_abiertas,
            'max_operaciones_por_simbolo': self.max_operaciones_por_simbolo
        }

class ConfigManager:
    """Gestor de configuración principal."""
    
    def __init__(self, config_path: str = 'configs/config.yml'):
        self.config_path = config_path
        self.config = self._cargar_config()
        
        # Inicializar sub-configuraciones
        self.mt5 = ConfigMT5(self.config.get('mt5', {}))
        self.trading = ConfigTrading(self.config.get('trading', {}))
        self.riesgo = ConfigRiesgo(self.config.get('risk', {}))
        self.indicadores = ConfigIndicadores(self.config.get('estrategia', {}))
        self.general = self.config.get('general', {})
    
    def _cargar_config(self) -> Dict[str, Any]:
        """Carga la configuración desde archivo YAML."""
        if not os.path.exists(self.config_path):
            print(f"⚠️  No se encontró {self.config_path}, usando configuración por defecto")
            return self._config_por_defecto()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"❌ Error cargando configuración: {e}")
            return self._config_por_defecto()
    
    def _config_por_defecto(self) -> Dict[str, Any]:
        """Configuración por defecto."""
        return {
            'mt5': {
                'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
                'login': 197991667,
                'password': 'Sudo@pt112006',
                'server': 'Exness-MT5Trial11',
                'timeout': 10000,
                'portable': False
            },
            'trading': {
                'simbolos': ['EURUSD', 'GBPUSD', 'XAUUSD'],
                'timeframe': 'M15',
                'lote_base': 0.1,
                'lote_maximo': 1.0,
                'lote_minimo': 0.01,
                'max_operaciones_abiertas': 3,
                'max_operaciones_por_simbolo': 1
            },
            'risk': {
                'riesgo_por_operacion': 2.0,
                'stop_loss_fijo_pips': 50,
                'take_profit_fijo_pips': 100,
                'max_drawdown_diario': 5.0,
                'max_drawdown_total': 20.0,
                'alerta_drawdown': 10.0
            },
            'estrategia': {
                'rsi_periodo': 14,
                'rsi_sobrecompra': 70,
                'rsi_sobreventa': 30,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'bb_periodo': 20,
                'bb_desviacion': 2.0
            },
            'general': {
                'modo': 'simulado',
                'log_level': 'INFO',
                'actualizar_intervalo': 60
            }
        }
    
    def guardar_config(self, config_path: Optional[str] = None):
        """Guarda la configuración actual en archivo."""
        save_path = config_path or self.config_path
        
        config_completa = {
            'mt5': self.mt5.to_dict(),
            'trading': self.trading.to_dict(),
            'risk': self.riesgo.to_dict(),
            'estrategia': self.indicadores.to_dict(),
            'general': self.general
        }
        
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_completa, f, default_flow_style=False, allow_unicode=True)
            print(f"✅ Configuración guardada en {save_path}")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
    
    def obtener_modo_actual(self) -> str:
        """Obtiene el modo actual (simulado/real)."""
        return self.general.get('modo', 'simulado')
    
    def obtener_config_completa(self) -> Dict[str, Any]:
        """Obtiene la configuración completa como diccionario."""
        return {
            'mt5': self.mt5.to_dict(),
            'trading': self.trading.to_dict(),
            'risk': self.riesgo.to_dict(),
            'estrategia': self.indicadores.to_dict(),
            'general': self.general
        }

def cargar_config(config_path: str = 'configs/config.yml') -> ConfigManager:
    """Carga la configuración desde archivo."""
    return ConfigManager(config_path)

def crear_config_por_defecto(config_path: str = 'configs/config.yml'):
    """Crea una configuración por defecto."""
    config = ConfigManager()
    config.guardar_config(config_path)
    print(f"✅ Configuración por defecto creada en {config_path}")
