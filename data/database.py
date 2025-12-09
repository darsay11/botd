"""
Módulo para persistencia de datos en SQLite.
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

class DatabaseManager:
    """Gestor de base de datos SQLite para el bot."""
    
    def __init__(self, db_path: str = "trading_bot.db"):
        """Inicializa el gestor de base de datos."""
        self.db_path = Path(db_path)
        self.connection = None
        self._inicializar_db()
        
    def _inicializar_db(self):
        """Inicializa la base de datos con las tablas necesarias."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            # Tabla de operaciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket TEXT UNIQUE,
                    simbolo TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    volumen REAL NOT NULL,
                    precio_apertura REAL NOT NULL,
                    precio_actual REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    comision REAL DEFAULT 0,
                    swap REAL DEFAULT 0,
                    beneficio REAL DEFAULT 0,
                    estado TEXT NOT NULL,
                    timestamp_apertura DATETIME NOT NULL,
                    timestamp_cierre DATETIME,
                    motivo_cierre TEXT,
                    senal_id INTEGER,
                    estrategia TEXT,
                    metadata TEXT
                )
            ''')
            
            # Tabla de señales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS senales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    simbolo TEXT NOT NULL,
                    direccion TEXT NOT NULL,
                    fuerza REAL,
                    precio_entrada REAL,
                    stop_loss_sugerido REAL,
                    take_profit_sugerido REAL,
                    razon_entrada TEXT,
                    confirmaciones TEXT,
                    accion_tomada TEXT,
                    metadata TEXT
                )
            ''')
            
            # Tabla de métricas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metricas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    tipo_metrica TEXT NOT NULL,
                    valor REAL NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # Tabla de logs del sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    nivel TEXT NOT NULL,
                    modulo TEXT,
                    mensaje TEXT NOT NULL,
                    excepcion TEXT
                )
            ''')
            
            # Índices para mejor rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_operaciones_simbolo ON operaciones(simbolo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_operaciones_estado ON operaciones(estado)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_operaciones_timestamp ON operaciones(timestamp_apertura)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_senales_timestamp ON senales(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metricas_timestamp ON metricas(timestamp)')
            
            self.connection.commit()
            logger.info(f"Base de datos inicializada: {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def guardar_operacion(self, operacion: Dict[str, Any]) -> int:
        """
        Guarda una operación en la base de datos.
        
        Args:
            operacion: Diccionario con datos de la operación
            
        Returns:
            ID de la operación insertada
        """
        try:
            cursor = self.connection.cursor()
            
            # Preparar valores
            valores = {
                'ticket': operacion.get('ticket'),
                'simbolo': operacion['simbolo'],
                'tipo': operacion['tipo'],
                'volumen': operacion['volumen'],
                'precio_apertura': operacion['precio_apertura'],
                'precio_actual': operacion.get('precio_actual'),
                'stop_loss': operacion.get('stop_loss'),
                'take_profit': operacion.get('take_profit'),
                'comision': operacion.get('comision', 0),
                'swap': operacion.get('swap', 0),
                'beneficio': operacion.get('beneficio', 0),
                'estado': operacion['estado'],
                'timestamp_apertura': operacion['timestamp_apertura'],
                'timestamp_cierre': operacion.get('timestamp_cierre'),
                'motivo_cierre': operacion.get('motivo_cierre'),
                'senal_id': operacion.get('senal_id'),
                'estrategia': operacion.get('estrategia'),
                'metadata': operacion.get('metadata', '{}')
            }
            
            # Construir consulta
            columnas = ', '.join(valores.keys())
            placeholders = ', '.join(['?'] * len(valores))
            query = f"INSERT INTO operaciones ({columnas}) VALUES ({placeholders})"
            
            cursor.execute(query, list(valores.values()))
            self.connection.commit()
            
            operacion_id = cursor.lastrowid
            logger.debug(f"Operación guardada: ID {operacion_id}")
            
            return operacion_id
            
        except sqlite3.Error as e:
            logger.error(f"Error guardando operación: {e}")
            self.connection.rollback()
            raise
    
    def actualizar_operacion(self, operacion_id: int, updates: Dict[str, Any]):
        """
        Actualiza una operación existente.
        
        Args:
            operacion_id: ID de la operación
            updates: Diccionario con campos a actualizar
        """
        try:
            if not updates:
                return
            
            cursor = self.connection.cursor()
            
            # Construir SET clause
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            valores = list(updates.values()) + [operacion_id]
            
            query = f"UPDATE operaciones SET {set_clause} WHERE id = ?"
            
            cursor.execute(query, valores)
            self.connection.commit()
            
            logger.debug(f"Operación {operacion_id} actualizada")
            
        except sqlite3.Error as e:
            logger.error(f"Error actualizando operación: {e}")
            self.connection.rollback()
            raise
    
    def obtener_operaciones(
        self, 
        filtros: Dict[str, Any] = None,
        limite: int = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene operaciones de la base de datos.
        
        Args:
            filtros: Diccionario con filtros
            limite: Límite de resultados
            
        Returns:
            Lista de operaciones
        """
        try:
            cursor = self.connection.cursor()
            
            # Construir consulta
            query = "SELECT * FROM operaciones"
            condiciones = []
            valores = []
            
            if filtros:
                for campo, valor in filtros.items():
                    if valor is not None:
                        condiciones.append(f"{campo} = ?")
                        valores.append(valor)
                
                if condiciones:
                    query += " WHERE " + " AND ".join(condiciones)
            
            query += " ORDER BY timestamp_apertura DESC"
            
            if limite:
                query += f" LIMIT {limite}"
            
            cursor.execute(query, valores)
            columnas = [desc[0] for desc in cursor.description]
            resultados = cursor.fetchall()
            
            # Convertir a diccionarios
            operaciones = []
            for fila in resultados:
                operacion = dict(zip(columnas, fila))
                operaciones.append(operacion)
            
            return operaciones
            
        except sqlite3.Error as e:
            logger.error(f"Error obteniendo operaciones: {e}")
            raise
    
    def guardar_senal(self, senal: Dict[str, Any]) -> int:
        """
        Guarda una señal en la base de datos.
        
        Args:
            senal: Diccionario con datos de la señal
            
        Returns:
            ID de la señal insertada
        """
        try:
            cursor = self.connection.cursor()
            
            # Preparar valores
            valores = {
                'timestamp': senal.get('timestamp', datetime.now()),
                'simbolo': senal['simbolo'],
                'direccion': senal['direccion'],
                'fuerza': senal.get('fuerza'),
                'precio_entrada': senal.get('precio_entrada'),
                'stop_loss_sugerido': senal.get('stop_loss_sugerido'),
                'take_profit_sugerido': senal.get('take_profit_sugerido'),
                'razon_entrada': senal.get('razon_entrada'),
                'confirmaciones': senal.get('confirmaciones', '[]'),
                'accion_tomada': senal.get('accion_tomada'),
                'metadata': senal.get('metadata', '{}')
            }
            
            # Construir consulta
            columnas = ', '.join(valores.keys())
            placeholders = ', '.join(['?'] * len(valores))
            query = f"INSERT INTO senales ({columnas}) VALUES ({placeholders})"
            
            cursor.execute(query, list(valores.values()))
            self.connection.commit()
            
            senal_id = cursor.lastrowid
            logger.debug(f"Señal guardada: ID {senal_id}")
            
            return senal_id
            
        except sqlite3.Error as e:
            logger.error(f"Error guardando señal: {e}")
            self.connection.rollback()
            raise
    
    def guardar_metrica(self, tipo_metrica: str, valor: float, metadata: str = None):
        """
        Guarda una métrica en la base de datos.
        
        Args:
            tipo_metrica: Tipo de métrica
            valor: Valor de la métrica
            metadata: Metadatos adicionales
        """
        try:
            cursor = self.connection.cursor()
            
            query = """
                INSERT INTO metricas (timestamp, tipo_metrica, valor, metadata)
                VALUES (?, ?, ?, ?)
            """
            
            cursor.execute(query, (datetime.now(), tipo_metrica, valor, metadata or '{}'))
            self.connection.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Error guardando métrica: {e}")
            self.connection.rollback()
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de las operaciones.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            cursor = self.connection.cursor()
            estadisticas = {}
            
            # Operaciones totales
            cursor.execute("SELECT COUNT(*) FROM operaciones")
            estadisticas['total_operaciones'] = cursor.fetchone()[0]
            
            # Operaciones cerradas
            cursor.execute("SELECT COUNT(*) FROM operaciones WHERE estado = 'cerrada'")
            estadisticas['operaciones_cerradas'] = cursor.fetchone()[0]
            
            # Win rate
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN beneficio > 0 THEN 1 END) as ganadoras,
                    COUNT(CASE WHEN beneficio < 0 THEN 1 END) as perdedoras
                FROM operaciones 
                WHERE estado = 'cerrada'
            """)
            ganadoras, perdedoras = cursor.fetchone()
            
            total_cerradas = ganadoras + perdedoras
            if total_cerradas > 0:
                estadisticas['win_rate'] = (ganadoras / total_cerradas) * 100
                estadisticas['ratio_ganancia_perdida'] = ganadoras / perdedoras if perdedoras > 0 else float('inf')
            else:
                estadisticas['win_rate'] = 0
                estadisticas['ratio_ganancia_perdida'] = 0
            
            # Beneficio total
            cursor.execute("SELECT SUM(beneficio) FROM operaciones WHERE estado = 'cerrada'")
            estadisticas['beneficio_total'] = cursor.fetchone()[0] or 0
            
            # Promedio ganadora y perdedora
            cursor.execute("SELECT AVG(beneficio) FROM operaciones WHERE estado = 'cerrada' AND beneficio > 0")
            estadisticas['promedio_ganadora'] = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(beneficio) FROM operaciones WHERE estado = 'cerrada' AND beneficio < 0")
            estadisticas['promedio_perdedora'] = cursor.fetchone()[0] or 0
            
            # Expectativa
            if estadisticas['promedio_ganadora'] > 0 and estadisticas['promedio_perdedora'] < 0:
                win_rate_decimal = estadisticas['win_rate'] / 100
                perdida_rate = 1 - win_rate_decimal
                estadisticas['expectativa'] = (
                    win_rate_decimal * estadisticas['promedio_ganadora'] + 
                    perdida_rate * estadisticas['promedio_perdedora']
                )
            else:
                estadisticas['expectativa'] = 0
            
            # Drawdown máximo
            cursor.execute("""
                SELECT MIN(beneficio_acumulado) FROM (
                    SELECT SUM(beneficio) OVER (ORDER BY timestamp_apertura) as beneficio_acumulado
                    FROM operaciones 
                    WHERE estado = 'cerrada'
                    ORDER BY timestamp_apertura
                )
            """)
            drawdown_min = cursor.fetchone()[0] or 0
            estadisticas['max_drawdown'] = abs(drawdown_min) if drawdown_min < 0 else 0
            
            return estadisticas
            
        except sqlite3.Error as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def exportar_a_csv(self, tabla: str, archivo_salida: str):
        """
        Exporta una tabla a archivo CSV.
        
        Args:
            tabla: Nombre de la tabla
            archivo_salida: Ruta del archivo de salida
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM {tabla}")
            
            import csv
            with open(archivo_salida, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([desc[0] for desc in cursor.description])
                writer.writerows(cursor.fetchall())
            
            logger.info(f"Tabla {tabla} exportada a {archivo_salida}")
            
        except Exception as e:
            logger.error(f"Error exportando tabla: {e}")
    
    def cerrar(self):
        """Cierra la conexión a la base de datos."""
        if self.connection:
            self.connection.close()
            logger.info("Conexión a base de datos cerrada")
    
    def __del__(self):
        """Destructor - cierra la conexión."""
        self.cerrar()