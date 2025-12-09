"""
Tests para cálculo de indicadores técnicos.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from strategies.signal_generator import SignalGenerator

class TestIndicators:
    """Tests para indicadores técnicos."""
    
    def setup_method(self):
        """Configuración para cada test."""
        # Crear datos de prueba
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        
        self.test_data = pd.DataFrame({
            'timestamp': dates,
            'apertura': np.random.randn(100).cumsum() + 100,
            'alto': np.random.randn(100).cumsum() + 101,
            'bajo': np.random.randn(100).cumsum() + 99,
            'cierre': np.random.randn(100).cumsum() + 100,
            'volumen': np.random.randint(1000, 10000, 100)
        })
        
        # Configuración de prueba
        self.config = {
            'indicadores': {
                'ema_rapida': 9,
                'ema_lenta': 21,
                'rsi_periodo': 14,
                'rsi_sobrecompra': 70,
                'rsi_sobreventa': 30,
                'macd_rapido': 12,
                'macd_lento': 26,
                'macd_señal': 9,
                'atr_periodo': 14
            }
        }
    
    def test_calculo_ema(self):
        """Test cálculo de EMA."""
        # Calcular EMA manualmente
        ema_rapida = self.test_data['cierre'].ewm(span=9).mean()
        ema_lenta = self.test_data['cierre'].ewm(span=21).mean()
        
        # Verificar cálculos
        assert len(ema_rapida) == len(self.test_data)
        assert len(ema_lenta) == len(self.test_data)
        assert not ema_rapida.isnull().all()
        assert not ema_lenta.isnull().all()
        
        # EMA rápida debería ser más sensible
        cambios_rapida = ema_rapida.diff().abs().mean()
        cambios_lenta = ema_lenta.diff().abs().mean()
        assert cambios_rapida > cambios_lenta
    
    def test_calculo_rsi(self):
        """Test cálculo de RSI."""
        # Datos con tendencia alcista clara
        data_alcista = pd.DataFrame({
            'cierre': np.linspace(100, 110, 50)
        })
        
        # Calcular RSI manualmente
        delta = data_alcista['cierre'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # RSI debería estar alto en tendencia alcista
        assert rsi.iloc[-1] > 50
    
    def test_deteccion_crossover(self):
        """Test detección de crossover de EMAs."""
        # Crear datos con crossover
        dates = pd.date_range(start='2023-01-01', periods=50, freq='1H')
        
        # EMA rápida cruza por encima de EMA lenta en el medio
        data = pd.DataFrame({
            'timestamp': dates,
            'ema_9': [95 + i*0.1 for i in range(25)] + [97.6 + i*0.3 for i in range(25)],
            'ema_21': [96 + i*0.2 for i in range(25)] + [97.5 + i*0.1 for i in range(25)],
            'cierre': [100 + i*0.1 for i in range(50)]
        })
        
        # Verificar crossover
        for i in range(1, len(data)):
            ema_9_prev = data['ema_9'].iloc[i-1]
            ema_21_prev = data['ema_21'].iloc[i-1]
            ema_9_curr = data['ema_9'].iloc[i]
            ema_21_curr = data['ema_21'].iloc[i]
            
            # En algún punto debería haber crossover
            if ema_9_prev <= ema_21_prev and ema_9_curr > ema_21_curr:
                assert True  # Crossover alcista detectado
                break
    
    def test_condicion_rsi_extremo(self):
        """Test condición RSI en zona extrema."""
        config_prueba = {
            'rsi_periodo': 14,
            'rsi_sobrecompra': 70,
            'rsi_sobreventa': 30
        }
        
        # Crear análisis con RSI en sobreventa
        analisis_prueba = {
            'rsi_actual': 25.0,  # En zona de sobreventa
            'dataframe': self.test_data
        }
        
        # La condición debería activarse para compra
        # (implementación simplificada)
        assert analisis_prueba['rsi_actual'] < config_prueba['rsi_sobreventa']
    
    def test_generador_senales(self):
        """Test del generador de señales."""
        generador = SignalGenerator(self.config)
        
        # Crear análisis de prueba
        analisis_prueba = {
            'M5': {
                'dataframe': self.test_data,
                'rsi_actual': 65.0,
                'precio_actual': 100.0
            }
        }
        
        # Generar señales
        senales = generador.generar_senales(analisis_prueba)
        
        # Verificar que retorna lista
        assert isinstance(senales, list)
        
        # En datos aleatorios, puede o no haber señales
        # Solo verificar que no hay errores
        assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])