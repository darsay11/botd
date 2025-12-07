# Bot de Trading Avanzado para MetaTrader 5

Un bot de trading automatizado desarrollado en Python que opera con MetaTrader 5. Incluye análisis de mercado en tiempo real, detección de estructuras avanzadas, gestión de riesgo profesional y sistema completo de backtesting.

## ✨ Características Principales

### 📊 Análisis de Mercado
- **Multi-timeframe**: Análisis simultáneo en H1, M15, M5, M1
- **Indicadores técnicos**: EMA, RSI, MACD, ATR, Volumen
- **Detección de estructuras**: Order Blocks, Zonas de Liquidez, Soportes/Resistencias
- **Análisis de volumen**: Confirmación de movimientos con volumen

### ⚡ Ejecución Inteligente
- **Conexión directa con MT5**: Operaciones en tiempo real
- **Modo simulado**: Backtesting y pruebas sin riesgo
- **Gestión de órdenes**: Protección contra duplicados, reintentos automáticos
- **Latencia controlada**: Gestión optimizada de ejecución

### 🛡️ Gestión de Riesgo Profesional
- **Cálculo dinámico de posición**: Basado en porcentaje de capital
- **Stop Loss inteligente**: Basado en ATR o niveles fijos
- **Take Profit automático**: Ratio riesgo/recompensa configurable
- **Trailing Stop y Break Even**: Gestión avanzada de posiciones

### 📈 Backtesting Completo
- **Simulación tick-by-tick**: Máxima precisión en resultados
- **Métricas detalladas**: Win Rate, Sharpe Ratio, Drawdown, Expectancy
- **Optimización de parámetros**: Grid search para mejora de estrategia
- **Reportes gráficos**: Curvas de equity, distribución de beneficios

### 🖥️ Interfaz Gráfica Moderna
- **Dashboard en tiempo real**: Estado del bot, métricas, capital
- **Gestión visual de operaciones**: Listado y control de posiciones
- **Configuración interactiva**: Ajuste de parámetros en caliente
- **Sistema de logging**: Visualización y exportación de logs

## 🚀 Instalación Rápida

### 1. Requisitos Previos
- Python 3.10 o superior
- MetaTrader 5 instalado (para modo real)
- Cuenta demo o real con un broker MT5

### 2. Clonar y Configurar
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/bot-trading-mt5.git
cd bot-trading-mt5

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt