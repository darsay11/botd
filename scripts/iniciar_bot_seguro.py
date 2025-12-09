#!/usr/bin/env python3
"""
Script para iniciar el bot de trading de manera segura.
Incluye validaciones de seguridad y confirmaciones.
"""
import os
import sys
import getpass
from pathlib import Path

# Añadir directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv, dotenv_values
from core.bot import BotTrading
from configs.config_manager import ConfigManager

def verificar_seguridad():
    """Verifica configuraciones de seguridad críticas."""
    print("\n" + "="*60)
    print("🔒 VERIFICACIÓN DE SEGURIDAD")
    print("="*60)
    
    # 1. Verificar archivo .env
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ No se encontró archivo .env")
        print("   Crea un archivo .env basado en .env.example")
        return False
    
    # 2. Cargar variables
    env_vars = dotenv_values(env_path)
    
    # 3. Verificar credenciales
    required_vars = ['MT5_SERVER', 'MT5_LOGIN', 'MT5_PASSWORD']
    missing_vars = [var for var in required_vars if var not in env_vars]
    
    if missing_vars:
        print(f"❌ Variables faltantes en .env: {', '.join(missing_vars)}")
        return False
    
    # 4. Advertencia modo real
    if env_vars.get('TRADING_MODE', 'simulado') == 'real':
        print("⚠️  ⚠️  ⚠️  ADVERTENCIA CRÍTICA ⚠️  ⚠️  ⚠️")
        print("   MODO REAL ACTIVADO - OPERARÁS CON DINERO REAL")
        print("   Verifica que estás usando una cuenta DEMO primero")
        
        confirm = input("\n¿Estás seguro de continuar? (solo 'SI' para confirmar): ")
        if confirm != "SI":
            print("❌ Inicio cancelado por el usuario")
            return False
    
    # 5. Verificar password no es demo
    password = env_vars.get('MT5_PASSWORD', '')
    if "demo" in password.lower() or "test" in password.lower():
        print("⚠️  Estás usando una contraseña demo")
        print("   Considera cambiar por seguridad")
    
    print("✅ Verificación de seguridad completada")
    return True

def mostrar_configuracion():
    """Muestra la configuración actual."""
    print("\n" + "="*60)
    print("⚙️  CONFIGURACIÓN ACTUAL")
    print("="*60)
    
    try:
        config = ConfigManager()
        
        # Información general
        modo = config.modo_actual
        print(f"📊 Modo operación: {modo}")
        
        if modo == 'real':
            mt5_config = config.obtener_config_mt5()
            print(f"📡 Servidor: {mt5_config.servidor}")
            print(f"👤 Login: {mt5_config.login}")
            print(f"🔐 Password: {'*' * len(mt5_config.password)}")
        
        # Parámetros trading
        general = config['general']
        print(f"\n📈 Parámetros Trading:")
        print(f"   Símbolo: {general.get('simbolo')}")
        print(f"   Lotaje mínimo: {general.get('lotaje_minimo')}")
        print(f"   Máx operaciones: {general.get('max_operaciones_abiertas')}")
        
        # Riesgo
        riesgo = config['riesgo']
        print(f"\n⚠️  Gestión de Riesgo:")
        print(f"   Riesgo por operación: {riesgo.get('porcentaje_por_operacion')}%")
        print(f"   Ratio R:R: {riesgo['take_profit'].get('ratio_riesgo_recompensa')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return False

def iniciar_bot_modo_seguro():
    """Inicia el bot con múltiples validaciones."""
    
    print("\n" + "="*60)
    print("🤖 BOT DE TRADING - INICIO SEGURO")
    print("="*60)
    
    # Paso 1: Verificar seguridad
    if not verificar_seguridad():
        print("❌ No se cumplen los requisitos de seguridad")
        return False
    
    # Paso 2: Mostrar configuración
    if not mostrar_configuracion():
        print("❌ Error en configuración")
        return False
    
    # Paso 3: Confirmación final
    print("\n" + "="*60)
    print("🚀 CONFIRMACIÓN DE INICIO")
    print("="*60)
    
    confirm = input("\n¿Deseas iniciar el bot con esta configuración? (si/no): ")
    if confirm.lower() != 'si':
        print("❌ Inicio cancelado por el usuario")
        return False
    
    # Paso 4: Iniciar bot
    try:
        print("\n🔄 Inicializando bot de trading...")
        bot = BotTrading()
        
        # Configurar antes de iniciar
        modo = ConfigManager().modo_actual
        if modo == 'real':
            print("⚠️  INICIANDO EN MODO REAL - EJECUTARÁ ÓRDENES REALES")
            print("   Monitorea constantemente el comportamiento")
        
        # Iniciar módulos
        bot.inicializar_modulos()
        
        # Mostrar mensaje final
        print("\n" + "="*60)
        print("✅ BOT INICIADO CORRECTAMENTE")
        print("="*60)
        print("\n📌 Instrucciones:")
        print("• El bot ejecutará ciclos de trading automáticamente")
        print("• Revisa los logs en tiempo real")
        print("• Para detener: Ctrl+C")
        print("• Reportes en carpeta 'reports/'")
        
        # Iniciar ciclo principal
        bot.iniciar()
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Bot detenido por usuario")
        return True
    except Exception as e:
        print(f"\n❌ Error iniciando bot: {e}")
        import traceback
        traceback.print_exc()
        return False

def menu_principal():
    """Menú principal interactivo."""
    while True:
        print("\n" + "="*60)
        print("🤖 MENÚ PRINCIPAL BOT TRADING")
        print("="*60)
        print("1. Iniciar bot de trading")
        print("2. Probar conexión con Exness")
        print("3. Ver configuración actual")
        print("4. Ejecutar backtesting demo")
        print("5. Salir")
        print("="*60)
        
        opcion = input("\nSelecciona una opción (1-5): ")
        
        if opcion == '1':
            iniciar_bot_modo_seguro()
        elif opcion == '2':
            from scripts.test_exness import probar_conexion_exness
            probar_conexion_exness()
        elif opcion == '3':
            mostrar_configuracion()
        elif opcion == '4':
            from scripts.run_backtest_demo import main as demo_main
            demo_main()
        elif opcion == '5':
            print("\n👋 Saliendo del bot de trading...")
            break
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    # Verificar Python 3.10+
    if sys.version_info < (3, 10):
        print("❌ Se requiere Python 3.10 o superior")
        sys.exit(1)
    
    # Verificar directorio
    if not Path("requirements.txt").exists():
        print("❌ No estás en el directorio correcto")
        print("   Navega a la carpeta del bot de trading")
        sys.exit(1)
    
    # Ejecutar menú
    menu_principal()