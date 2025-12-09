"""
Tests para módulo de ejecución (broker).
"""
import pytest
from datetime import datetime
from execution.broker import BrokerSimulado, Orden, ResultadoOrden

class TestBroker:
    """Tests para el módulo de broker."""
    
    def setup_method(self):
        """Configuración para cada test."""
        self.config = {
            'backtesting': {
                'capital_inicial': 10000,
                'comision_por_lote': 2.5,
                'spread_promedio': 2.0
            }
        }
        
        self.broker = BrokerSimulado(self.config)
    
    def test_colocar_orden_compra(self):
        """Test colocación de orden de compra."""
        orden = Orden(
            simbolo='EURUSD',
            tipo='COMPRA',
            volumen=0.1,
            precio=1.10000,
            stop_loss=1.09800,
            take_profit=1.10400,
            comentario='Test compra'
        )
        
        resultado = self.broker.colocar_orden(orden)
        
        # Verificar resultado
        assert resultado.exito
        assert resultado.ticket is not None
        assert resultado.precio is not None
        assert resultado.volumen == 0.1
        
        # Verificar que se creó posición
        posiciones = self.broker.obtener_posiciones_abiertas()
        assert len(posiciones) == 1
        assert posiciones[0]['ticket'] == resultado.ticket
    
    def test_colocar_orden_venta(self):
        """Test colocación de orden de venta."""
        orden = Orden(
            simbolo='EURUSD',
            tipo='VENTA',
            volumen=0.1,
            precio=1.10000,
            stop_loss=1.10200,
            take_profit=1.09600,
            comentario='Test venta'
        )
        
        resultado = self.broker.colocar_orden(orden)
        
        # Verificar resultado
        assert resultado.exito
        assert resultado.ticket is not None
        
        # Verificar que se creó posición
        posiciones = self.broker.obtener_posiciones_abiertas()
        assert len(posiciones) == 1
    
    def test_cerrar_orden(self):
        """Test cierre de orden."""
        # Primero colocar orden
        orden = Orden(
            simbolo='EURUSD',
            tipo='COMPRA',
            volumen=0.1,
            precio=1.10000
        )
        
        resultado_apertura = self.broker.colocar_orden(orden)
        
        # Cerrar orden
        resultado_cierre = self.broker.cerrar_orden(resultado_apertura.ticket)
        
        # Verificar cierre exitoso
        assert resultado_cierre.exito
        
        # Verificar que no hay posiciones abiertas
        posiciones = self.broker.obtener_posiciones_abiertas()
        assert len(posiciones) == 0
        
        # Verificar historial
        historial = self.broker.obtener_historial()
        assert len(historial) == 1
    
    def test_estado_cuenta(self):
        """Test obtención de estado de cuenta."""
        estado = self.broker.obtener_estado_cuenta()
        
        # Verificar estructura
        assert 'balance' in estado
        assert 'equity' in estado
        assert 'beneficio' in estado
        
        # Balance inicial debe ser $10,000
        assert estado['balance'] == 10000
        
        # Equity inicial igual a balance
        assert estado['equity'] == 10000
    
    def test_comision_calculo(self):
        """Test cálculo de comisiones."""
        orden = Orden(
            simbolo='EURUSD',
            tipo='COMPRA',
            volumen=1.0,  # 1 lote
            precio=1.10000
        )
        
        resultado = self.broker.colocar_orden(orden)
        assert resultado.exito
        
        # Verificar que se restó comisión
        estado = self.broker.obtener_estado_cuenta()
        
        # Comisión esperada: 1.0 * 2.5 = $2.5
        # Balance: 10000 - 2.5 = 9997.5
        assert estado['balance'] == 10000 - 2.5
    
    def test_modificar_orden(self):
        """Test modificación de orden."""
        # Colocar orden
        orden = Orden(
            simbolo='EURUSD',
            tipo='COMPRA',
            volumen=0.1,
            precio=1.10000,
            stop_loss=1.09800,
            take_profit=1.10400
        )
        
        resultado = self.broker.colocar_orden(orden)
        
        # Modificar stop loss y take profit
        cambios = {
            'stop_loss': 1.09900,
            'take_profit': 1.10500
        }
        
        resultado_mod = self.broker.modificar_orden(resultado.ticket, cambios)
        
        # Verificar modificación exitosa
        assert resultado_mod.exito
        
        # Verificar cambios en posición
        posiciones = self.broker.obtener_posiciones_abiertas()
        posicion = posiciones[0]
        
        assert posicion['stop_loss'] == 1.09900
        assert posicion['take_profit'] == 1.10500
    
    def test_orden_con_precio_none(self):
        """Test orden sin precio especificado."""
        orden = Orden(
            simbolo='EURUSD',
            tipo='COMPRA',
            volumen=0.1
            # precio=None por defecto
        )
        
        resultado = self.broker.colocar_orden(orden)
        
        # Debería usar precio simulado
        assert resultado.exito
        assert resultado.precio is not None
    
    def test_volumen_minimo(self):
        """Test volumen mínimo."""
        orden = Orden(
            simbolo='EURUSD',
            tipo='COMPRA',
            volumen=0.001  # Menor que mínimo
        )
        
        # Debería lanzar error
        with pytest.raises(ValueError):
            self.broker.colocar_orden(orden)
    
    def test_multiple_operaciones(self):
        """Test múltiples operaciones simultáneas."""
        # Colocar varias órdenes
        for i in range(3):
            orden = Orden(
                simbolo='EURUSD',
                tipo='COMPRA',
                volumen=0.1,
                precio=1.10000 + i*0.001
            )
            self.broker.colocar_orden(orden)
        
        # Verificar múltiples posiciones
        posiciones = self.broker.obtener_posiciones_abiertas()
        assert len(posiciones) == 3
        
        # Cerrar todas
        for posicion in posiciones:
            self.broker.cerrar_orden(posicion['ticket'])
        
        # Verificar historial
        historial = self.broker.obtener_historial()
        assert len(historial) == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])