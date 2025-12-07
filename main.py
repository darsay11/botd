#!/usr/bin/env python3
"""
Punto de entrada principal del Bot de Trading Avanzado para MetaTrader 5.

Este script permite ejecutar el bot en diferentes modos:
- GUI: Interfaz gráfica con customtkinter
- CLI: Línea de comandos para operación en segundo plano
- Backtest: Modo de backtesting y optimización
- Demo: Demostración con datos de prueba
"""

import sys
import os
import argparse
from pathlib import Path
from loguru import logger

# Añadir directorio actual al path para importaciones
sys.path.insert(0, str(Path(__file__).parent))

def configurar_logging(nivel: str = "INFO"):
    """Configura el sistema de logging."""
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar loguru
    logger.remove()  # Remover handler por defecto
    
    # Log a archivo
    logger.add(
        log_dir / "trading_bot_{time}.log",
        rotation="10 MB",
        retention="30 days",
        level=nivel,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
        compression="zip"
    )
    
    # Log a consola con colores
    logger.add(
        sys.stdout,
        level=nivel,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    return logger

def modo_gui():
    """Ejecuta el bot en modo interfaz gráfica."""
    try:
        logger.info("Iniciando interfaz gráfica...")
        
        # Importar aquí para evitar dependencias si no se usa GUI
        from ui.main_window import MainWindow
        import customtkinter as ctk
        
        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Crear y ejecutar aplicación
        app = MainWindow()
        app.run()
        
        logger.info("Interfaz gráfica finalizada")
        
    except ImportError as e:
        logger.error(f"Error importando módulos de GUI: {e}")
        logger.info("Instala customtkinter: pip install customtkinter")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error en modo GUI: {e}")
        sys.exit(1)

def modo_cli(config_path: str):
    """Ejecuta el bot en modo línea de comandos."""
    try:
        logger.info("Iniciando modo línea de comandos...")
        
        from core.bot import BotTrading
        
        # Crear instancia del bot
        bot = BotTrading(config_path)
        
        # Inicializar módulos
        logger.info("Inicializando módulos...")
        bot.inicializar_modulos()
        
        # Mostrar advertencia si es modo real
        if bot.config.obtener_modo_actual() == 'real':
            logger.warning("=" * 60)
            logger.warning("⚠️  MODO REAL ACTIVADO - OPERACIONES CON DINERO REAL")
            logger.warning("=" * 60)
            
            respuesta = input("\n¿Continuar con modo real? (si/NO): ")
            if respuesta.lower() != 'si':
                logger.info("Operación cancelada por usuario")
                sys.exit(0)
        
        # Iniciar bot
        logger.info("Iniciando bot de trading...")
        bot.iniciar()
        
        # Mantener el programa ejecutándose
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nDetención solicitada por usuario (Ctrl+C)")
            bot.detener()
            
    except KeyboardInterrupt:
        logger.info("Operación cancelada por usuario")
    except Exception as e:
        logger.error(f"Error en modo CLI: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def modo_backtest(config_path: str):
    """Ejecuta backtesting."""
    try:
        logger.info("Iniciando modo backtesting...")
        
        from backtest.backtest_engine import BacktestEngine
        from data.market_data import MarketData
        import pandas as pd
        from datetime import datetime
        
        # Cargar configuración
        from configs.config_manager import ConfigManager
        config = ConfigManager(config_path)
        
        # Crear motor de backtesting
        backtester = BacktestEngine(config)
        
        # Cargar datos de prueba
        logger.info("Cargando datos para backtesting...")
        
        # Para demo, crear datos sintéticos si no hay conexión MT5
        try:
            mercado = MarketData(config)
            if mercado.conectar_mt5():
                # Descargar datos reales
                datos = mercado.obtener_velas_multi_timeframe(
                    config['general']['simbolo'],
                    ['H1', 'M15', 'M5']
                )
                mercado.desconectar_mt5()
            else:
                # Crear datos sintéticos
                logger.warning("No hay conexión MT5, usando datos sintéticos")
                datos = crear_datos_sinteticos()
        except:
            # Crear datos sintéticos como fallback
            datos = crear_datos_sinteticos()
        
        # Cargar datos en el backtester
        backtester.cargar_datos(datos)
        
        # Ejecutar backtesting
        logger.info("Ejecutando backtesting...")
        resultados = backtester.ejecutar()
        
        # Mostrar resultados
        if resultados.get('metricas'):
            metricas = resultados['metricas']
            logger.info("\n" + "="*60)
            logger.info("📊 RESULTADOS BACKTESTING")
            logger.info("="*60)
            logger.info(f"Total operaciones: {metricas.get('total_operaciones', 0)}")
            logger.info(f"Win Rate: {metricas.get('win_rate', 0):.2f}%")
            logger.info(f"Beneficio total: ${metricas.get('beneficio_total', 0):.2f}")
            logger.info(f"Retorno: {metricas.get('retorno_total', 0):.2f}%")
            logger.info(f"Drawdown máximo: {metricas.get('drawdown_maximo', 0):.2f}%")
            logger.info(f"Sharpe Ratio: {metricas.get('sharpe_ratio', 0):.3f}")
            logger.info("="*60)
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        
        # Guardar métricas
        if resultados.get('metricas'):
            df_metricas = pd.DataFrame([resultados['metricas']])
            df_metricas.to_csv(report_dir / f"metricas_{timestamp}.csv", index=False)
            
        # Guardar operaciones
        if resultados.get('operaciones'):
            df_operaciones = pd.DataFrame(resultados['operaciones'])
            df_operaciones.to_csv(report_dir / f"operaciones_{timestamp}.csv", index=False)
        
        logger.info(f"Resultados guardados en: {report_dir}/")
        
    except Exception as e:
        logger.error(f"Error en backtesting: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def crear_datos_sinteticos() -> dict:
    """Crea datos sintéticos para demostración."""
    import numpy as np
    import pandas as pd
    from datetime import datetime, timedelta
    
    logger.info("Generando datos sintéticos para demo...")
    
    datos = {}
    timeframes = ['H1', 'M15', 'M5']
    
    for tf in timeframes:
        # Determinar número de velas según timeframe
        if tf == 'H1':
            n_velas = 24 * 30  # 30 días
            minutos_por_vela = 60
        elif tf == 'M15':
            n_velas = 96 * 30  # 30 días
            minutos_por_vela = 15
        else:  # M5
            n_velas = 288 * 30  # 30 días
            minutos_por_vela = 5
        
        # Crear timestamps
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        timestamps = pd.date_range(start=start_time, end=end_time, 
                                 periods=n_velas, freq=f'{minutos_por_vela}min')
        
        # Crear precios con tendencia y volatilidad
        np.random.seed(42)  # Para reproducibilidad
        base_price = 1.10000
        returns = np.random.normal(0.0001, 0.001, n_velas)  # Tendencia alcista suave
        
        prices = base_price * (1 + np.cumsum(returns))
        
        # Crear DataFrame con OHLC
        df = pd.DataFrame({
            'timestamp': timestamps,
            'apertura': prices * (1 + np.random.normal(0, 0.0001, n_velas)),
            'alto': prices * (1 + np.abs(np.random.normal(0.0002, 0.0002, n_velas))),
            'bajo': prices * (1 - np.abs(np.random.normal(0.0002, 0.0002, n_velas))),
            'cierre': prices,
            'volumen': np.random.randint(100, 10000, n_velas),
            'spread': np.random.uniform(1, 3, n_velas)
        })
        
        # Asegurar que high > low
        df['alto'] = df[['alto', 'bajo', 'cierre']].max(axis=1)
        df['bajo'] = df[['alto', 'bajo', 'cierre']].min(axis=1)
        
        datos[tf] = df
    
    logger.info(f"Datos sintéticos generados: {len(datos)} timeframes")
    return datos

def modo_demo():
    """Ejecuta una demostración completa del bot."""
    try:
        logger.info("Iniciando demostración del bot...")
        
        print("\n" + "="*60)
        print("🤖 DEMOSTRACIÓN BOT DE TRADING")
        print("="*60)
        
        print("\n1. Probando conexión MT5...")
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                print("   ✅ MT5 conectado correctamente")
                mt5.shutdown()
            else:
                print("   ⚠️  No se pudo conectar a MT5 (modo demo continuará)")
        except:
            print("   ⚠️  MT5 no disponible (modo demo continuará)")
        
        print("\n2. Probando estrategias...")
        from strategies.advanced_strategy import AdvancedStrategy
        from configs.config_manager import ConfigManager
        
        config = ConfigManager()
        estrategia = AdvancedStrategy(config)
        print(f"   ✅ Estrategia '{estrategia.nombre}' cargada")
        
        print("\n3. Probando gestión de riesgo...")
        from risk.risk_manager import RiskManager
        gestor_riesgo = RiskManager(config)
        metricas = gestor_riesgo.obtener_metricas_riesgo()
        print(f"   ✅ Gestor de riesgo configurado")
        print(f"   Capital: ${metricas.get('capital', 0):.2f}")
        print(f"   Riesgo/operación: {metricas.get('riesgo_por_operacion', 0)}%")
        
        print("\n4. Probando backtesting...")
        datos = crear_datos_sinteticos()
        print(f"   ✅ Datos generados: {len(datos['H1'])} velas H1")
        
        print("\n5. Ejecutando simulación rápida...")
        from execution.broker import BrokerSimulado
        broker = BrokerSimulado(config.config)
        
        # Simular algunas operaciones
        from execution.broker import Orden
        orden = Orden(
            simbolo="EURUSD",
            tipo="COMPRA",
            volumen=0.1,
            precio=1.10000,
            stop_loss=1.09800,
            take_profit=1.10400,
            comentario="Demo"
        )
        
        resultado = broker.colocar_orden(orden)
        if resultado.exito:
            print(f"   ✅ Orden demo colocada: Ticket {resultado.ticket}")
            
            # Cerrar orden
            broker.cerrar_orden(resultado.ticket)
            print(f"   ✅ Orden demo cerrada")
            
            # Mostrar resultados
            estado = broker.obtener_estado_cuenta()
            print(f"   Balance final: ${estado.get('balance', 0):.2f}")
        else:
            print(f"   ⚠️  No se pudo colocar orden demo")
        
        print("\n" + "="*60)
        print("🎉 DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        
        print("\n📋 Pasos siguientes:")
        print("1. Configura tus credenciales en .env")
        print("2. Prueba con: python main.py --modo backtest")
        print("3. Ejecuta en simulado: python main.py --modo cli")
        print("4. Usa interfaz gráfica: python main.py --modo gui")
        
        print("\n⚠️  Recuerda:")
        print("- Nunca operes con dinero real sin probar extensamente")
        print("- Siempre comienza en modo simulado")
        print("- Monitorea los logs en tiempo real")
        
    except Exception as e:
        logger.error(f"Error en demostración: {e}")
        print(f"\n❌ Error en demostración: {e}")

def verificar_requisitos():
    """Verifica que se cumplan los requisitos del sistema."""
    print("\n" + "="*60)
    print("🔍 VERIFICANDO REQUISITOS DEL SISTEMA")
    print("="*60)
    
    problemas = []
    
    # 1. Verificar Python 3.10+
    if sys.version_info < (3, 10):
        problemas.append("Se requiere Python 3.10 o superior")
    
    # 2. Verificar archivos necesarios
    archivos_requeridos = [
        "requirements.txt",
        "configs/config.yml",
        "core/bot.py"
    ]
    
    for archivo in archivos_requeridos:
        if not Path(archivo).exists():
            problemas.append(f"Falta archivo: {archivo}")
    
    # 3. Verificar .env (solo advertencia)
    if not Path(".env").exists():
        print("⚠️  Advertencia: No se encontró archivo .env")
        print("   Crea uno basado en .env.example")
    
    # 4. Verificar directorios
    directorios = ["logs", "reports", "configs", "core", "data", 
                   "strategies", "execution", "risk", "backtest", "ui", "tests"]
    
    for directorio in directorios:
        if not Path(directorio).exists():
            print(f"⚠️  Advertencia: Directorio '{directorio}' no existe")
            print(f"   Creando directorio...")
            Path(directorio).mkdir(exist_ok=True)
    
    if problemas:
        print("\n❌ PROBLEMAS ENCONTRADOS:")
        for problema in problemas:
            print(f"   • {problema}")
        print("\nSoluciona estos problemas antes de continuar.")
        return False
    
    print("\n✅ Todos los requisitos verificados correctamente")
    return True

def main():
    """Función principal del bot de trading."""
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(
        description='Bot de Trading Avanzado para MetaTrader 5',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s --modo gui              # Interfaz gráfica
  %(prog)s --modo cli              # Línea de comandos
  %(prog)s --modo backtest         # Backtesting
  %(prog)s --demo                  # Demostración
  %(prog)s --config mi_config.yml  # Configuración personalizada
  
Modos disponibles:
  gui      - Interfaz gráfica (recomendado para principiantes)
  cli      - Línea de comandos (para servidores/background)
  backtest - Backtesting y optimización
        """
    )
    
    parser.add_argument('--modo', choices=['gui', 'cli', 'backtest'], 
                       default='gui', help='Modo de ejecución (default: gui)')
    parser.add_argument('--config', type=str, default='configs/config.yml',
                       help='Ruta al archivo de configuración')
    parser.add_argument('--demo', action='store_true',
                       help='Ejecutar demostración del bot')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Nivel de logging')
    parser.add_argument('--version', action='version', version='Bot Trading v1.0.0')
    
    args = parser.parse_args()
    
    # Banner inicial
    print("\n" + "="*60)
    print("🤖 BOT DE TRADING AVANZADO - MT5")
    print("="*60)
    print(f"Python {sys.version}")
    print(f"Directorio: {Path.cwd()}")
    print("="*60)
    
    # Verificar requisitos
    if not verificar_requisitos():
        sys.exit(1)
    
    # Configurar logging
    logger = configurar_logging(args.log_level)
    
    logger.info("=" * 60)
    logger.info("INICIANDO BOT DE TRADING")
    logger.info("=" * 60)
    logger.info(f"Modo: {args.modo}")
    logger.info(f"Configuración: {args.config}")
    logger.info(f"Log level: {args.log_level}")
    
    try:
        if args.demo:
            # Modo demostración
            modo_demo()
            
        elif args.modo == 'gui':
            # Modo interfaz gráfica
            modo_gui()
            
        elif args.modo == 'cli':
            # Modo línea de comandos
            modo_cli(args.config)
            
        elif args.modo == 'backtest':
            # Modo backtesting
            modo_backtest(args.config)
            
    except KeyboardInterrupt:
        logger.info("\nOperación cancelada por usuario (Ctrl+C)")
    except Exception as e:
        logger.error(f"Error en ejecución principal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        logger.info("=" * 60)
        logger.info("BOT DE TRADING FINALIZADO")
        logger.info("=" * 60)

if __name__ == "__main__":
    # Establecer encoding UTF-8
    if sys.platform.startswith('win'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # Ejecutar aplicación
    main()