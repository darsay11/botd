"""
Paquete strategies - Estrategias de trading.
"""

from .base_strategy import BaseStrategy, Señal
from .advanced_strategy import AdvancedStrategy
from .signal_generator import SignalGenerator

__all__ = [
    'BaseStrategy',
    'Señal',
    'AdvancedStrategy',
    'SignalGenerator'
]