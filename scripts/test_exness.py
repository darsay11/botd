#!/usr/bin/env python3
"""
Script para probar conexión con servidor Exness MT5.
"""
import os
import sys
from pathlib import Path

# Añadir directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

def probar_conexion_exness():
    """Prueba completa de conexión con Exness."""
    
    print("\n" + "="*60)
    print("🔌 PRUEBA DE CONEXIÓN EXNESS MT5")
    print("="*60)
    
    # 1. Cargar configuración
    load_dotenv()
    
    server = os.getenv('MT5_SERVER')
    login = os.getenv('MT5_LOGIN')
    password = os.getenv('MT5_PASSWORD')
    
    if not all([server, login, password]):
        print("❌ Error: Faltan credenciales en .env")
        print("   Verifica que MT5_SERVER, MT5_LOGIN y MT5_PASSWORD estén configurados")
        return False
    
    print(f"📡 Conectando a: {server}")
    print(f"👤 Login: {login}")
    print(f"🔐 Password: {'*' * len(password)}")
    
    try:
        # 2. Intentar conexión
        print("\n🔄 Inicializando MT5...")
        if not mt5.initialize(
            login=int(login),
            password=password,
            server=server,
            timeout=10000,
            portable=False
        ):
            error = mt5.last_error()
            print(f"❌ Error de conexión: {error}")
            
            # Errores comunes específicos de Exness
            if "account disabled" in str(error).lower():
                print("\n⚠️  Problema común: Cuenta demo expirada")
                print("   Las cuentas demo de Exness expiran en 30 días")
                print("   Solución: Solicita nueva cuenta demo en exness.com")
            elif "invalid account" in str(error).lower():
                print("\n⚠️  Credenciales incorrectas")
                print("   Verifica login y password")
                print("   Prueba crear nueva cuenta demo")
            elif "no connection" in str(error).lower():
                print("\n⚠️  Problema de red")
                print("   Verifica tu conexión a internet")
                print("   Prueba cambiar servidor a Exness-MT5Trial[1-20]")
            elif "not authorized" in str(error).lower():
                print("\n⚠️  No autorizado")
                print("   La cuenta puede estar bloqueada")
                print("   Contacta soporte de Exness")
            
            return False
        
        print("✅ Conexión establecida exitosamente")
        
        # 3. Obtener información de cuenta
        print("\n📊 INFORMACIÓN DE CUENTA EXNESS:")
        print("-" * 40)
        
        account = mt5.account_info()
        if account:
            print(f"   Nombre: {account.name}")
            print(f"   Balance: ${account.balance:.2f}")
            print(f"   Equity: ${account.equity:.2f}")
            print(f"   Moneda: {account.currency}")
            print(f"   Apalancamiento: 1:{account.leverage}")
            print(f"   Margen libre: ${account.margin_free:.2f}")
            print(f"   Nivel margen: {account.margin_level:.2f}%")
            print(f"   Servidor: {account.server}")
            print(f"   Tipo cuenta: {'Demo' if account.trade_mode == 0 else 'Real'}")
        else:
            print("   No se pudo obtener información de cuenta")
        
        # 4. Verificar símbolos disponibles
        print("\n📈 SÍMBOLOS DISPONIBLES EXNESS:")
        print("-" * 40)
        
        symbols = mt5.symbols_get()
        if symbols:
            print(f"   Total símbolos: {len(symbols)}")
            
            # Filtrar principales
            principales = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']
            disponibles = [s for s in symbols if s.name in principales]
            
            if disponibles:
                print("   Principales disponibles:")
                for symbol in disponibles[:5]:
                    print(f"   • {symbol.name}: Spread={symbol.spread}")
            else:
                print("   No se encontraron los símbolos principales")
                print("   Mostrando primeros 5 símbolos:")
                for symbol in symbols[:5]:
                    print(f"   • {symbol.name}")
        else:
            print("   No se pudieron obtener símbolos")
        
        # 5. Probar descarga de datos
        print("\n📥 PRUEBA DE DESCARGA DE DATOS:")
        print("-" * 40)
        
        symbol_test = "EURUSD"
        rates = mt5.copy_rates_from(symbol_test, mt5.TIMEFRAME_H1, 
                                   datetime.now() - timedelta(days=1), 10)
        
        if rates is not None and len(rates) > 0:
            print(f"   ✅ Datos descargados para {symbol_test}")
            print(f"   Velas obtenidas: {len(rates)}")
            
            # Convertir a DataFrame para mostrar
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            print(f"   Rango de fechas: {df['time'].min()} a {df['time'].max()}")
            print(f"   Último precio: {df['close'].iloc[-1]:.5f}")
        else:
            print(f"   ❌ No se pudieron descargar datos para {symbol_test}")
        
        # 6. Verificar horarios de trading
        print("\n🕐 HORARIOS DE TRADING EXNESS:")
        print("-" * 40)
        
        symbol_info = mt5.symbol_info(symbol_test)
        if symbol_info:
            print(f"   Símbolo: {symbol_info.name}")
            print(f"   Punto: {symbol_info.point}")
            print(f"   Dígitos: {symbol_info.digits}")
            print(f"   Spread actual: {symbol_info.spread}")
            print(f"   Margen inicial: {symbol_info.margin_initial}")
            print(f"   Sesión trading: {symbol_info.time_start} - {symbol_info.time_end}")
        else:
            print(f"   No se obtuvo info detallada para {symbol_test}")
        
        # 7. Cerrar conexión
        mt5.shutdown()
        print("\n🔒 Conexión cerrada correctamente")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def mostrar_ayuda_exness():
    """Muestra ayuda específica para Exness."""
    print("\n" + "="*60)
    print("🆘 AYUDA PARA CONFIGURACIÓN EXNESS")
    print("="*60)
    
    print("\n📌 PASOS PARA RESOLVER PROBLEMAS:")
    print("1. Verifica que tengas MetaTrader 5 instalado")
    print("2. Asegúrate de que tu cuenta demo no haya expirado")
    print("3. Prueba diferentes servidores:")
    print("   - Exness-MT5Trial1")
    print("   - Exness-MT5Trial2")
    print("   - ... hasta Exness-MT5Trial20")
    print("4. Crea nueva cuenta demo si es necesario")
    print("5. Verifica tu conexión a internet")
    
    print("\n📞 SOPORTE EXNESS:")
    print("• Sitio web: https://www.exness.com")
    print("• Soporte 24/7: Chat en vivo en el sitio")
    print("• Comunidad: https://community.exness.com")
    
    print("\n⚠️ RECOMENDACIONES:")
    print("• Siempre prueba primero en modo SIMULADO")
    print("• Usa cuenta DEMO por al menos 2 semanas")
    print("• Empieza con capital mínimo ($100 en demo)")
    print("• Monitoriza constantemente las operaciones")

if __name__ == "__main__":
    # Ejecutar prueba
    success = probar_conexion_exness()
    
    print("\n" + "="*60)
    if success:
        print("🎉 PRUEBA EXITOSA - Tu configuración Exness funciona")
        print("   Puedes proceder a usar el bot de trading")
    else:
        print("❌ PRUEBA FALLIDA - Hay problemas de conexión")
        print("   Revisa la configuración y sigue las instrucciones")
        
        mostrar_ayuda_exness()
    
    print("="*60)
    
    # Preguntar si quiere ver la configuración actual
    respuesta = input("\n¿Ver configuración actual? (s/n): ")
    if respuesta.lower() == 's':
        from configs.config_manager import ConfigManager
        config = ConfigManager()
        print(f"\nModo actual: {config.modo_actual}")
        print(f"Símbolo: {config.config.get('general', {}).get('simbolo')}")
        print(f"Servidor: {config.config.get('mt5', {}).get('servidor')}")