"""
Tests para gestión de riesgo.
"""
import pytest
import numpy as np
from risk.risk_manager import RiskManager

class TestRiskManagement:
    """Tests para gestión de riesgo."""
    
    def setup_method(self):
        """Configuración para cada test."""
        self.config = {
            'riesgo': {
                'porcentaje_por_operacion': 2.0,
                'riesgo_maximo_diario': 10.0,
                'stop_loss': {
                    'tipo': 'atr',
                    'multiplicador_atr': 1.5,
                    'puntos_fijo': 20,
                    'porcentaje': 1.0
                },
                'take_profit': {
                    'tipo': 'rr',
                    'ratio_riesgo_recompensa': 2.0,
                    'puntos_fijo': 40,
                    'porcentaje': 2.0
                }
            },
            'general': {
                'lotaje_minimo': 0.01
            },
            'backtesting': {
                'capital_inicial': 10000
            }
        }
        
        self.risk_manager = RiskManager(self.config)
    
    def test_calculo_volumen(self):
        """Test cálculo de volumen basado en riesgo."""
        # Crear señal de prueba
        senal_prueba = {
            'simbolo': 'EURUSD',
            'direccion': 'COMPRA',
            'precio_entrada': 1.10000,
            'fuerza': 75,
            'confirmaciones': ['crossover_ema', 'rsi_extremo'],
            'metadata': {'atr': 0.0010}
        }
        
        # Calcular volumen
        volumen = self.risk_manager._calcular_volumen(senal_prueba)
        
        # Verificar que el volumen es positivo
        assert volumen > 0
        
        # Verificar que cumple con mínimo
        assert volumen >= self.config['general']['lotaje_minimo']
        
        # Verificar que es un valor razonable para el capital
        # 2% de $10,000 = $200 de riesgo
        # Con SL de ~15 pips (1.5 * ATR), valor por pip ~$1 por 0.1 lote
        # Volumen esperado ~1.33 lotes
        assert 0.1 <= volumen <= 5.0
    
    def test_calculo_stop_loss_atr(self):
        """Test cálculo de stop loss basado en ATR."""
        senal_prueba = {
            'direccion': 'COMPRA',
            'precio_entrada': 1.10000,
            'metadata': {'atr': 0.0010}
        }
        
        stop_loss = self.risk_manager._calcular_stop_loss(senal_prueba)
        
        # Para compra, SL debe ser menor que precio de entrada
        assert stop_loss < senal_prueba['precio_entrada']
        
        # Distancia debe ser 1.5 * ATR
        distancia_esperada = 0.0010 * 1.5
        distancia_real = senal_prueba['precio_entrada'] - stop_loss
        
        # Verificar con tolerancia
        assert abs(distancia_real - distancia_esperada) < 0.0001
    
    def test_calculo_take_profit_rr(self):
        """Test cálculo de take profit basado en ratio riesgo/recompensa."""
        senal_prueba = {
            'direccion': 'COMPRA',
            'precio_entrada': 1.10000
        }
        
        stop_loss = 1.09850  # 15 pips de distancia
        
        take_profit = self.risk_manager._calcular_take_profit(senal_prueba, stop_loss)
        
        # Para compra, TP debe ser mayor que precio de entrada
        assert take_profit > senal_prueba['precio_entrada']
        
        # Ratio riesgo/recompensa debe ser 2:1
        distancia_sl = senal_prueba['precio_entrada'] - stop_loss
        distancia_tp = take_profit - senal_prueba['precio_entrada']
        ratio = distancia_tp / distancia_sl
        
        # Verificar ratio
        assert abs(ratio - 2.0) < 0.1
    
    def test_validacion_senal(self):
        """Test validación de señales."""
        # Señal válida
        senal_valida = {
            'fuerza': 75,
            'confirmaciones': ['cond1', 'cond2', 'cond3']
        }
        
        # Señal inválida (fuerza baja)
        senal_invalida_fuerza = {
            'fuerza': 30,
            'confirmaciones': ['cond1', 'cond2']
        }
        
        # Señal inválida (confirmaciones insuficientes)
        senal_invalida_confirmaciones = {
            'fuerza': 80,
            'confirmaciones': ['cond1']
        }
        
        # Verificar validaciones
        assert self.risk_manager.validar_senal(senal_valida)
        assert not self.risk_manager.validar_senal(senal_invalida_fuerza)
        assert not self.risk_manager.validar_senal(senal_invalida_confirmaciones)
    
    def test_riesgo_acumulado(self):
        """Test cálculo de riesgo acumulado."""
        # Simular múltiples operaciones
        self.risk_manager.operaciones_hoy = 5
        self.risk_manager.riesgo_acumulado_hoy = 0.08  # 8%
        
        # Crear señal
        senal_prueba = {
            'precio_entrada': 1.10000,
            'metadata': {'atr': 0.0010}
        }
        
        stop_loss = 1.09850
        
        # Actualizar riesgo
        self.risk_manager._actualizar_riesgo_acumulado(senal_prueba, stop_loss)
        
        # Verificar que se actualizó
        assert self.risk_manager.operaciones_hoy == 6
        assert self.risk_manager.riesgo_acumulado_hoy > 0.08
    
    def test_limite_riesgo_diario(self):
        """Test límite de riesgo diario."""
        # Configurar riesgo acumulado alto
        self.risk_manager.riesgo_acumulado_hoy = 0.11  # 11%, por encima del 10% máximo
        
        senal_prueba = {
            'fuerza': 80,
            'confirmaciones': ['cond1', 'cond2']
        }
        
        # La señal no debería ser válida (riesgo diario excedido)
        assert not self.risk_manager.validar_senal(senal_prueba)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])