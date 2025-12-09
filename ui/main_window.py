# ui/main_window.py - INTERFAZ PROFESIONAL
import customtkinter as ctk
import threading
import time
from datetime import datetime
import random
from loguru import logger

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainWindow:
    """Interfaz gráfica profesional para el bot de trading."""
    
    def __init__(self):
        self.app = ctk.CTk()
        self.setup_window()
        self.create_widgets()
        self.running = False
        self.connected = False
        self.prices = {}
        
    def setup_window(self):
        """Configurar ventana principal."""
        self.app.title("🤖 ALGO TRADER PRO - MT5")
        self.app.geometry("1200x800")
        self.app.minsize(1000, 700)
        
        # Centrar ventana
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 800) // 2
        self.app.geometry(f"1200x800+{x}+{y}")
        
    def create_widgets(self):
        """Crear todos los widgets de la interfaz."""
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.app)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 1. BARRA SUPERIOR - Estado y conexión
        self.create_top_bar()
        
        # 2. PANEL IZQUIERDO - Control y estadísticas
        self.create_left_panel()
        
        # 3. PANEL CENTRAL - Gráficos y precios
        self.create_center_panel()
        
        # 4. PANEL DERECHO - Órdenes y logs
        self.create_right_panel()
        
        # 5. BARRA INFERIOR - Botones de acción
        self.create_bottom_bar()
        
    def create_top_bar(self):
        """Crear barra superior de estado."""
        top_frame = ctk.CTkFrame(self.main_frame, height=60)
        top_frame.pack(fill="x", padx=10, pady=(10, 5))
        top_frame.pack_propagate(False)
        
        # Logo y título
        title_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            title_frame,
            text="🤖",
            font=("Arial", 28)
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="ALGO TRADER PRO",
            font=("Arial", 22, "bold")
        ).pack(side="left")
        
        # Estado de conexión
        self.connection_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        self.connection_frame.pack(side="right", padx=20)
        
        self.connection_status = ctk.CTkLabel(
            self.connection_frame,
            text="● DESCONECTADO",
            text_color="red",
            font=("Arial", 14, "bold")
        )
        self.connection_status.pack(side="left", padx=(0, 10))
        
        self.connect_btn = ctk.CTkButton(
            self.connection_frame,
            text="CONECTAR MT5",
            width=120,
            command=self.connect_mt5
        )
        self.connect_btn.pack(side="left")
        
    def create_left_panel(self):
        """Crear panel izquierdo de control."""
        left_frame = ctk.CTkFrame(self.main_frame, width=300)
        left_frame.pack(side="left", fill="y", padx=(10, 5), pady=5)
        left_frame.pack_propagate(False)
        
        # 1. Información de cuenta
        account_frame = ctk.CTkFrame(left_frame)
        account_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            account_frame,
            text="📊 CUENTA",
            font=("Arial", 16, "bold")
        ).pack(pady=(10, 5))
        
        self.account_labels = {}
        account_info = [
            ("Número:", "197991667"),
            ("Nombre:", "Standard"),
            ("Tipo:", "Demo"),
            ("Moneda:", "USD"),
            ("Apalancamiento:", "1:100")
        ]
        
        for label, value in account_info:
            frame = ctk.CTkFrame(account_frame, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(
                frame,
                text=label,
                font=("Arial", 12),
                width=100,
                anchor="w"
            ).pack(side="left")
            
            lbl = ctk.CTkLabel(
                frame,
                text=value,
                font=("Arial", 12, "bold"),
                text_color="#2Ecc71"
            )
            lbl.pack(side="right")
            self.account_labels[label] = lbl
        
        # 2. Balance y equity
        balance_frame = ctk.CTkFrame(left_frame)
        balance_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            balance_frame,
            text="💰 BALANCE",
            font=("Arial", 16, "bold")
        ).pack(pady=(10, 5))
        
        self.balance_value = ctk.CTkLabel(
            balance_frame,
            text="$5,000.00",
            font=("Arial", 28, "bold"),
            text_color="#2Ecc71"
        )
        self.balance_value.pack(pady=5)
        
        self.equity_value = ctk.CTkLabel(
            balance_frame,
            text="Equity: $5,000.00",
            font=("Arial", 14)
        )
        self.equity_value.pack(pady=(0, 10))
        
        # 3. Configuración de riesgo
        risk_frame = ctk.CTkFrame(left_frame)
        risk_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            risk_frame,
            text="⚠️ GESTIÓN DE RIESGO",
            font=("Arial", 16, "bold")
        ).pack(pady=(10, 5))
        
        # Slider de riesgo por operación
        ctk.CTkLabel(
            risk_frame,
            text="Riesgo por operación:",
            font=("Arial", 12)
        ).pack(anchor="w", padx=10)
        
        self.risk_slider = ctk.CTkSlider(
            risk_frame,
            from_=0.5,
            to=5,
            number_of_steps=10,
            width=250
        )
        self.risk_slider.set(2.0)
        self.risk_slider.pack(padx=10, pady=5)
        
        self.risk_label = ctk.CTkLabel(
            risk_frame,
            text="2.0%",
            font=("Arial", 12, "bold")
        )
        self.risk_label.pack()
        
        self.risk_slider.configure(command=self.update_risk_label)
        
    def create_center_panel(self):
        """Crear panel central con gráficos y precios."""
        center_frame = ctk.CTkFrame(self.main_frame)
        center_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # 1. Tabs para diferentes vistas
        self.center_tabs = ctk.CTkTabview(center_frame)
        self.center_tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab 1: Precios en tiempo real
        self.prices_tab = self.center_tabs.add("📈 PRECIOS")
        self.create_prices_tab()
        
        # Tab 2: Gráfico
        self.chart_tab = self.center_tabs.add("📊 GRÁFICO")
        self.create_chart_tab()
        
        # Tab 3: Análisis técnico
        self.analysis_tab = self.center_tabs.add("🔍 ANÁLISIS")
        self.create_analysis_tab()
        
    def create_prices_tab(self):
        """Crear tab de precios en tiempo real."""
        # Frame para la tabla de precios
        prices_frame = ctk.CTkFrame(self.prices_tab)
        prices_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Encabezados de la tabla
        headers_frame = ctk.CTkFrame(prices_frame, height=40)
        headers_frame.pack(fill="x", pady=(0, 5))
        headers_frame.pack_propagate(False)
        
        headers = ["SÍMBOLO", "BID", "ASK", "SPREAD", "ALTO", "BAJO", "VOLUMEN"]
        widths = [100, 100, 100, 80, 100, 100, 100]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(
                headers_frame,
                text=header,
                font=("Arial", 12, "bold"),
                width=width
            ).pack(side="left", padx=2)
        
        # Frame para los precios (con scroll)
        self.prices_scroll_frame = ctk.CTkScrollableFrame(prices_frame)
        self.prices_scroll_frame.pack(fill="both", expand=True)
        
        # Diccionario para almacenar labels de precios
        self.price_widgets = {}
        
        # Inicializar con algunos símbolos
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD", "ETHUSD"]
        for symbol in symbols:
            self.add_price_row(symbol)
        
        # Actualizar precios periódicamente
        self.update_realtime_prices()
    
    def add_price_row(self, symbol):
        """Añadir una fila de precio para un símbolo."""
        row_frame = ctk.CTkFrame(self.prices_scroll_frame, height=35)
        row_frame.pack(fill="x", pady=1)
        row_frame.pack_propagate(False)
        
        widgets = {}
        
        # Símbolo
        widgets['symbol'] = ctk.CTkLabel(
            row_frame,
            text=symbol,
            font=("Arial", 11, "bold"),
            width=100
        )
        widgets['symbol'].pack(side="left", padx=2)
        
        # Bid
        widgets['bid'] = ctk.CTkLabel(
            row_frame,
            text="1.08545",
            font=("Consolas", 11),
            width=100
        )
        widgets['bid'].pack(side="left", padx=2)
        
        # Ask
        widgets['ask'] = ctk.CTkLabel(
            row_frame,
            text="1.08547",
            font=("Consolas", 11),
            width=100
        )
        widgets['ask'].pack(side="left", padx=2)
        
        # Spread
        widgets['spread'] = ctk.CTkLabel(
            row_frame,
            text="2.0",
            font=("Consolas", 11),
            width=80,
            text_color="orange"
        )
        widgets['spread'].pack(side="left", padx=2)
        
        # High
        widgets['high'] = ctk.CTkLabel(
            row_frame,
            text="1.08600",
            font=("Consolas", 11),
            width=100
        )
        widgets['high'].pack(side="left", padx=2)
        
        # Low
        widgets['low'] = ctk.CTkLabel(
            row_frame,
            text="1.08400",
            font=("Consolas", 11),
            width=100
        )
        widgets['low'].pack(side="left", padx=2)
        
        # Volume
        widgets['volume'] = ctk.CTkLabel(
            row_frame,
            text="1.2M",
            font=("Consolas", 11),
            width=100
        )
        widgets['volume'].pack(side="left", padx=2)
        
        self.price_widgets[symbol] = widgets
    
    def create_chart_tab(self):
        """Crear tab de gráfico (simulado)."""
        chart_frame = ctk.CTkFrame(self.chart_tab)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título del gráfico
        ctk.CTkLabel(
            chart_frame,
            text="EURUSD - Gráfico en Tiempo Real",
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Frame para controles del gráfico
        chart_controls = ctk.CTkFrame(chart_frame)
        chart_controls.pack(fill="x", padx=10, pady=5)
        
        # Timeframes
        timeframes = ["M1", "M5", "M15", "H1", "H4", "D1"]
        for tf in timeframes:
            btn = ctk.CTkButton(
                chart_controls,
                text=tf,
                width=50,
                height=25
            )
            btn.pack(side="left", padx=2)
        
        # Área del gráfico (simulado)
        chart_area = ctk.CTkFrame(chart_frame, height=400)
        chart_area.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Simulación de gráfico con texto
        chart_text = ctk.CTkTextbox(chart_area, font=("Consolas", 10))
        chart_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Generar "gráfico" ASCII
        chart_ascii = """
        ┌─────────────────────────────────────────┐
        │                  EURUSD                 │
        │ 1.08700 ┤            ╭─╮               │
        │         │           ╭╯ ╰╮              │
        │ 1.08600 ┤         ╭─╯   ╰─╮            │
        │         │       ╭─╯       ╰─╮          │
        │ 1.08500 ┤     ╭─╯           ╰─╮        │
        │         │   ╭─╯               ╰─╮      │
        │ 1.08400 ┤ ╭─╯                   ╰─╮    │
        │         │╭╯                       ╰╮   │
        │ 1.08300 ┼───────────────────────────   │
        │         0   2   4   6   8   10  12 hrs │
        └─────────────────────────────────────────┘
        """
        chart_text.insert("1.0", chart_ascii)
        chart_text.configure(state="disabled")
    
    def create_analysis_tab(self):
        """Crear tab de análisis técnico."""
        analysis_frame = ctk.CTkFrame(self.analysis_tab)
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Indicadores
        indicators_frame = ctk.CTkFrame(analysis_frame)
        indicators_frame.pack(fill="both", expand=True)
        
        # RSI
        rsi_frame = ctk.CTkFrame(indicators_frame)
        rsi_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            rsi_frame,
            text="RSI (14):",
            font=("Arial", 12)
        ).pack(side="left", padx=10)
        
        self.rsi_value = ctk.CTkLabel(
            rsi_frame,
            text="45.3",
            font=("Arial", 12, "bold"),
            text_color="orange"
        )
        self.rsi_value.pack(side="left", padx=10)
        
        rsi_progress = ctk.CTkProgressBar(rsi_frame, width=200)
        rsi_progress.set(0.453)
        rsi_progress.pack(side="left", padx=10)
        
        # MACD
        macd_frame = ctk.CTkFrame(indicators_frame)
        macd_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            macd_frame,
            text="MACD:",
            font=("Arial", 12)
        ).pack(side="left", padx=10)
        
        self.macd_value = ctk.CTkLabel(
            macd_frame,
            text="-0.00012",
            font=("Arial", 12, "bold"),
            text_color="red"
        )
        self.macd_value.pack(side="left", padx=10)
        
        # Señales
        signals_frame = ctk.CTkFrame(analysis_frame)
        signals_frame.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkLabel(
            signals_frame,
            text="SEÑALES DE TRADING:",
            font=("Arial", 14, "bold")
        ).pack(pady=5)
        
        self.signal_label = ctk.CTkLabel(
            signals_frame,
            text="🔍 ANALIZANDO MERCADO...",
            font=("Arial", 16),
            text_color="yellow"
        )
        self.signal_label.pack(pady=10)
    
    def create_right_panel(self):
        """Crear panel derecho con órdenes y logs."""
        right_frame = ctk.CTkFrame(self.main_frame, width=350)
        right_frame.pack(side="right", fill="y", padx=(5, 10), pady=5)
        right_frame.pack_propagate(False)
        
        # Tabs para órdenes y logs
        self.right_tabs = ctk.CTkTabview(right_frame)
        self.right_tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab 1: Órdenes abiertas
        self.orders_tab = self.right_tabs.add("📋 ÓRDENES")
        self.create_orders_tab()
        
        # Tab 2: Historial
        self.history_tab = self.right_tabs.add("📜 HISTORIAL")
        self.create_history_tab()
        
        # Tab 3: Logs
        self.logs_tab = self.right_tabs.add("📝 LOGS")
        self.create_logs_tab()
    
    def create_orders_tab(self):
        """Crear tab de órdenes abiertas."""
        orders_frame = ctk.CTkFrame(self.orders_tab)
        orders_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Encabezados
        headers_frame = ctk.CTkFrame(orders_frame, height=30)
        headers_frame.pack(fill="x", pady=(0, 5))
        
        headers = ["PAR", "TIPO", "LOTE", "PRECIO", "P&L"]
        for header in headers:
            ctk.CTkLabel(
                headers_frame,
                text=header,
                font=("Arial", 11, "bold")
            ).pack(side="left", padx=10, expand=True)
        
        # Lista de órdenes (vacía por ahora)
        self.orders_list_frame = ctk.CTkScrollableFrame(orders_frame)
        self.orders_list_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            self.orders_list_frame,
            text="No hay órdenes abiertas",
            font=("Arial", 12),
            text_color="gray"
        ).pack(pady=50)
    
    def create_history_tab(self):
        """Crear tab de historial de operaciones."""
        history_frame = ctk.CTkFrame(self.history_tab)
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Texto de historial
        history_text = ctk.CTkTextbox(history_frame, font=("Consolas", 10))
        history_text.pack(fill="both", expand=True)
        
        # Historial simulado
        history_data = """
        FECHA       PAR      TIPO   LOTE   ENTRADA  SALIDA   P&L
        ---------------------------------------------------------
        2024-01-15  EURUSD   BUY    0.1    1.08500  1.08650  +$15.00
        2024-01-14  GBPUSD   SELL   0.1    1.27000  1.26850  +$15.00
        2024-01-13  XAUUSD   BUY    0.01   2020.00  2025.00  +$5.00
        2024-01-12  EURUSD   SELL   0.2    1.09000  1.08800  +$40.00
        2024-01-11  BTCUSD   BUY    0.001  42000    42500    +$5.00
        """
        history_text.insert("1.0", history_data)
        history_text.configure(state="disabled")
    
    def create_logs_tab(self):
        """Crear tab de logs del sistema."""
        logs_frame = ctk.CTkFrame(self.logs_tab)
        logs_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.logs_text = ctk.CTkTextbox(
            logs_frame,
            font=("Consolas", 10),
            wrap="word"
        )
        self.logs_text.pack(fill="both", expand=True)
        
        # Logs iniciales
        self.add_log("Sistema inicializado")
        self.add_log("Interfaz gráfica cargada")
        self.add_log("Listo para conectar a MT5")
    
    def create_bottom_bar(self):
        """Crear barra inferior de control."""
        bottom_frame = ctk.CTkFrame(self.main_frame, height=60)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))
        bottom_frame.pack_propagate(False)
        
        # Botón principal de START/STOP
        self.main_action_btn = ctk.CTkButton(
            bottom_frame,
            text="🚀 INICIAR BOT",
            font=("Arial", 16, "bold"),
            height=45,
            width=200,
            command=self.toggle_bot,
            fg_color="#27ae60",
            hover_color="#219653"
        )
        self.main_action_btn.pack(side="left", padx=20)
        
        # Estadísticas rápidas
        stats_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        stats_frame.pack(side="left", padx=20)
        
        self.stats_labels = {}
        stats = [
            ("Operaciones:", "0"),
            ("Win Rate:", "0%"),
            ("P&L Total:", "$0.00"),
            ("Drawdown:", "0%")
        ]
        
        for label, value in stats:
            frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            frame.pack(side="left", padx=10)
            
            ctk.CTkLabel(
                frame,
                text=label,
                font=("Arial", 11)
            ).pack(side="left")
            
            lbl = ctk.CTkLabel(
                frame,
                text=value,
                font=("Arial", 11, "bold"),
                text_color="#2Ecc71"
            )
            lbl.pack(side="left", padx=(5, 0))
            self.stats_labels[label] = lbl
        
        # Reloj en tiempo real
        self.clock_label = ctk.CTkLabel(
            bottom_frame,
            text="00:00:00",
            font=("Consolas", 14),
            width=100
        )
        self.clock_label.pack(side="right", padx=20)
        
        # Iniciar reloj
        self.update_clock()
    
    # ===== FUNCIONALIDADES =====
    
    def connect_mt5(self):
        """Simular conexión a MT5."""
        self.connected = True
        self.connection_status.configure(
            text="● CONECTADO",
            text_color="#2Ecc71"
        )
        self.connect_btn.configure(text="✅ CONECTADO", state="disabled")
        self.add_log("Conectado a MT5 - Exness-MT5Trial11")
        self.add_log("Cuenta: 197991667 - Balance: $5,000.00")
        
        # Habilitar botón de inicio
        self.main_action_btn.configure(state="normal")
    
    def toggle_bot(self):
        """Iniciar/detener el bot."""
        if not self.running:
            self.start_bot()
        else:
            self.stop_bot()
    
    def start_bot(self):
        """Iniciar el bot de trading."""
        self.running = True
        self.main_action_btn.configure(
            text="⏹️ DETENER BOT",
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        self.add_log("Bot de trading iniciado")
        self.add_log("Monitoreando mercados...")
        
        # Actualizar señal
        self.signal_label.configure(
            text="✅ BUSCANDO OPORTUNIDADES...",
            text_color="#2Ecc71"
        )
    
    def stop_bot(self):
        """Detener el bot de trading."""
        self.running = False
        self.main_action_btn.configure(
            text="🚀 INICIAR BOT",
            fg_color="#27ae60",
            hover_color="#219653"
        )
        self.add_log("Bot de trading detenido")
        self.signal_label.configure(
            text="🔍 ANALIZANDO MERCADO...",
            text_color="yellow"
        )
    
    def update_realtime_prices(self):
        """Actualizar precios en tiempo real."""
        def update():
            while True:
                if hasattr(self, 'price_widgets'):
                    for symbol, widgets in self.price_widgets.items():
                        # Simular cambios de precio
                        if symbol == "EURUSD":
                            base = 1.08500
                        elif symbol == "GBPUSD":
                            base = 1.26500
                        elif symbol == "USDJPY":
                            base = 148.000
                        elif symbol == "XAUUSD":
                            base = 2020.00
                        elif symbol == "BTCUSD":
                            base = 42000.00
                        else:
                            base = 2200.00
                        
                        # Variación aleatoria
                        change = random.uniform(-0.001, 0.001)
                        if symbol == "XAUUSD" or symbol == "BTCUSD":
                            change *= 10
                        
                        bid = base + change
                        ask = bid + random.uniform(0.0001, 0.0003)
                        spread = (ask - bid) * 10000
                        
                        # Actualizar widgets
                        self.app.after(0, lambda s=symbol, b=bid, a=ask, sp=spread: 
                            self.update_price_widget(s, b, a, sp))
                
                time.sleep(1)
        
        thread = threading.Thread(target=update, daemon=True)
        thread.start()
    
    def update_price_widget(self, symbol, bid, ask, spread):
        """Actualizar un widget de precio."""
        if symbol in self.price_widgets:
            widgets = self.price_widgets[symbol]
            
            # Formatear según el símbolo
            if "USD" in symbol and "XAU" not in symbol and "BTC" not in symbol:
                bid_fmt = f"{bid:.5f}"
                ask_fmt = f"{ask:.5f}"
            else:
                bid_fmt = f"{bid:.2f}"
                ask_fmt = f"{ask:.2f}"
            
            widgets['bid'].configure(text=bid_fmt)
            widgets['ask'].configure(text=ask_fmt)
            widgets['spread'].configure(text=f"{spread:.1f}")
            
            # Cambiar color del spread según valor
            if spread < 2:
                color = "#2Ecc71"  # Verde
            elif spread < 5:
                color = "#f39c12"  # Naranja
            else:
                color = "#e74c3c"  # Rojo
            
            widgets['spread'].configure(text_color=color)
    
    def update_risk_label(self, value):
        """Actualizar label del slider de riesgo."""
        self.risk_label.configure(text=f"{float(value):.1f}%")
    
    def update_clock(self):
        """Actualizar reloj en tiempo real."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=current_time)
        self.app.after(1000, self.update_clock)
    
    def add_log(self, message):
        """Añadir mensaje al log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.logs_text.configure(state="normal")
        self.logs_text.insert("end", log_entry)
        self.logs_text.see("end")
        self.logs_text.configure(state="disabled")
    
    def run(self):
        """Ejecutar la aplicación."""
        self.app.mainloop()

# ===== EJECUCIÓN DIRECTA =====
if __name__ == "__main__":
    try:
        app = TradingGUI()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")