"""
Generador de reportes para backtesting.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import json
from loguru import logger

class BacktestReporter:
    """Genera reportes y gráficos de backtesting."""
    
    def __init__(self):
        """Inicializa el generador de reportes."""
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def generar_reporte(self, resultados: Dict, config: Dict):
        """
        Genera reporte completo de backtesting.
        
        Args:
            resultados: Resultados del backtesting
            config: Configuración usada
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. Generar reporte de texto
            self._generar_reporte_texto(resultados, config, timestamp)
            
            # 2. Generar gráficos
            self._generar_graficos(resultados, timestamp)
            
            # 3. Exportar datos
            self._exportar_datos(resultados, timestamp)
            
            logger.info(f"Reporte generado: reports/backtest_{timestamp}.txt")
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
    
    def _generar_reporte_texto(self, resultados: Dict, config: Dict, timestamp: str):
        """Genera reporte de texto."""
        try:
            metricas = resultados.get('metricas', {})
            operaciones = resultados.get('operaciones', [])
            
            with open(self.reports_dir / f"backtest_{timestamp}.txt", 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("REPORTE DE BACKTESTING - BOT DE TRADING AVANZADO\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Rango de fechas: {config['backtesting']['fecha_inicio']} - {config['backtesting']['fecha_fin']}\n")
                f.write(f"Capital inicial: ${config['backtesting']['capital_inicial']:,.2f}\n")
                f.write(f"Símbolo: {config['general']['simbolo']}\n")
                f.write(f"Modo: {config['general']['modo']}\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("MÉTRICAS DE RENDIMIENTO\n")
                f.write("-" * 80 + "\n\n")
                
                if metricas:
                    f.write(f"Total operaciones: {metricas.get('total_operaciones', 0)}\n")
                    f.write(f"Operaciones ganadoras: {metricas.get('operaciones_ganadoras', 0)}\n")
                    f.write(f"Operaciones perdedoras: {metricas.get('operaciones_perdedoras', 0)}\n")
                    f.write(f"Win Rate: {metricas.get('win_rate', 0):.2f}%\n")
                    f.write(f"Beneficio total: ${metricas.get('beneficio_total', 0):,.2f}\n")
                    f.write(f"Retorno total: {metricas.get('retorno_total', 0):.2f}%\n")
                    f.write(f"Retorno anualizado: {metricas.get('retorno_anualizado', 0):.2f}%\n")
                    f.write(f"Drawdown máximo: {metricas.get('drawdown_maximo', 0):.2f}%\n")
                    f.write(f"Sharpe Ratio: {metricas.get('sharpe_ratio', 0):.3f}\n")
                    f.write(f"Expectancy: ${metricas.get('expectancy', 0):.2f}\n\n")
                else:
                    f.write("No hay métricas disponibles\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("RESUMEN DE OPERACIONES\n")
                f.write("-" * 80 + "\n\n")
                
                if operaciones:
                    df_operaciones = pd.DataFrame(operaciones)
                    
                    # Resumen por tipo
                    compras = df_operaciones[df_operaciones['tipo'] == 'COMPRA']
                    ventas = df_operaciones[df_operaciones['tipo'] == 'VENTA']
                    
                    f.write(f"Operaciones de COMPRA: {len(compras)}\n")
                    f.write(f"Operaciones de VENTA: {len(ventas)}\n\n")
                    
                    # Top 5 mejores operaciones
                    mejores = df_operaciones.nlargest(5, 'beneficio')
                    f.write("TOP 5 MEJORES OPERACIONES:\n")
                    for _, op in mejores.iterrows():
                        f.write(f"  Ticket {op['ticket']}: {op['tipo']} {op['volumen']:.2f} "
                              f"@ {op['precio_apertura']:.5f}, Beneficio: ${op['beneficio']:.2f}\n")
                    
                    f.write("\n")
                    
                    # Top 5 peores operaciones
                    peores = df_operaciones.nsmallest(5, 'beneficio')
                    f.write("TOP 5 PEORES OPERACIONES:\n")
                    for _, op in peores.iterrows():
                        f.write(f"  Ticket {op['ticket']}: {op['tipo']} {op['volumen']:.2f} "
                              f"@ {op['precio_apertura']:.5f}, Beneficio: ${op['beneficio']:.2f}\n")
                    
                    f.write("\n")
                    
                    # Estadísticas por mes
                    if 'timestamp_apertura' in df_operaciones.columns:
                        df_operaciones['timestamp_apertura'] = pd.to_datetime(df_operaciones['timestamp_apertura'])
                        df_operaciones['mes'] = df_operaciones['timestamp_apertura'].dt.strftime('%Y-%m')
                        
                        beneficio_mensual = df_operaciones.groupby('mes')['beneficio'].sum()
                        
                        f.write("BENEFICIO MENSUAL:\n")
                        for mes, beneficio in beneficio_mensual.items():
                            f.write(f"  {mes}: ${beneficio:,.2f}\n")
                    
                else:
                    f.write("No hay operaciones para mostrar\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("CONFIGURACIÓN USADA\n")
                f.write("-" * 80 + "\n\n")
                
                # Escribir configuración relevante
                config_importante = {
                    'general': config['general'],
                    'indicadores': config['indicadores'],
                    'riesgo': config['riesgo']
                }
                
                f.write(json.dumps(config_importante, indent=2, ensure_ascii=False))
                f.write("\n\n")
                
                f.write("=" * 80 + "\n")
                f.write("FIN DEL REPORTE\n")
                f.write("=" * 80 + "\n")
                
        except Exception as e:
            logger.error(f"Error generando reporte de texto: {e}")
    
    def _generar_graficos(self, resultados: Dict, timestamp: str):
        """Genera gráficos de resultados."""
        try:
            equity_curve = resultados.get('equity_curve', [])
            
            if not equity_curve:
                logger.warning("No hay datos para gráficos")
                return
            
            # Convertir a DataFrame
            df_equity = pd.DataFrame(equity_curve)
            df_equity['timestamp'] = pd.to_datetime(df_equity['timestamp'])
            
            # Gráfico 1: Curva de equity
            plt.figure(figsize=(12, 6))
            plt.plot(df_equity['timestamp'], df_equity['equity'], label='Equity', linewidth=2)
            plt.plot(df_equity['timestamp'], df_equity['balance'], label='Balance', linewidth=1, alpha=0.7)
            plt.xlabel('Fecha')
            plt.ylabel('Capital ($)')
            plt.title('Curva de Equity')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(self.reports_dir / f"equity_curve_{timestamp}.png", dpi=150)
            plt.close()
            
            # Gráfico 2: Drawdown
            if 'drawdowns' in resultados and resultados['drawdowns']:
                drawdowns = resultados['drawdowns']
                
                plt.figure(figsize=(12, 4))
                plt.fill_between(range(len(drawdowns)), drawdowns, 0, alpha=0.3, color='red')
                plt.plot(drawdowns, color='red', linewidth=1)
                plt.xlabel('Período')
                plt.ylabel('Drawdown (%)')
                plt.title('Drawdown Histórico')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(self.reports_dir / f"drawdown_{timestamp}.png", dpi=150)
                plt.close()
            
            # Gráfico 3: Distribución de beneficios
            operaciones = resultados.get('operaciones', [])
            if operaciones:
                df_ops = pd.DataFrame(operaciones)
                beneficios = df_ops['beneficio'].values
                
                plt.figure(figsize=(10, 6))
                plt.hist(beneficios, bins=30, edgecolor='black', alpha=0.7)
                plt.axvline(x=0, color='red', linestyle='--', linewidth=1)
                plt.xlabel('Beneficio ($)')
                plt.ylabel('Frecuencia')
                plt.title('Distribución de Beneficios por Operación')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(self.reports_dir / f"distribucion_beneficios_{timestamp}.png", dpi=150)
                plt.close()
            
            logger.info(f"Gráficos generados: reports/*_{timestamp}.png")
            
        except Exception as e:
            logger.error(f"Error generando gráficos: {e}")
    
    def _exportar_datos(self, resultados: Dict, timestamp: str):
        """Exporta datos a archivos CSV."""
        try:
            # Exportar operaciones
            operaciones = resultados.get('operaciones', [])
            if operaciones:
                df_ops = pd.DataFrame(operaciones)
                df_ops.to_csv(self.reports_dir / f"operaciones_{timestamp}.csv", index=False, encoding='utf-8')
            
            # Exportar curva de equity
            equity_curve = resultados.get('equity_curve', [])
            if equity_curve:
                df_equity = pd.DataFrame(equity_curve)
                df_equity.to_csv(self.reports_dir / f"equity_curve_{timestamp}.csv", index=False, encoding='utf-8')
            
            # Exportar métricas
            metricas = resultados.get('metricas', {})
            if metricas:
                df_metricas = pd.DataFrame([metricas])
                df_metricas.to_csv(self.reports_dir / f"metricas_{timestamp}.csv", index=False, encoding='utf-8')
            
            logger.info(f"Datos exportados: reports/*_{timestamp}.csv")
            
        except Exception as e:
            logger.error(f"Error exportando datos: {e}")