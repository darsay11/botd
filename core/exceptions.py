class ErrorConfiguracion(Exception):
    """Excepción para errores de configuración."""
    def __init__(self, mensaje="Error en la configuración", detalle=""):
        self.mensaje = mensaje
        self.detalle = detalle
        super().__init__(f"{mensaje}: {detalle}" if detalle else mensaje)

class ErrorConexionMT5(Exception):
    """Excepción para errores de conexión con MT5."""
    def __init__(self, error_code=0, mensaje="Error de conexión MT5"):
        self.error_code = error_code
        self.mensaje = mensaje
        super().__init__(f"MT5 Error {error_code}: {mensaje}")

class ErrorOperacion(Exception):
    """Excepción para errores en operaciones de trading."""
    def __init__(self, simbolo="", tipo="", mensaje="Error en operación"):
        self.simbolo = simbolo
        self.tipo = tipo
        self.mensaje = mensaje
        super().__init__(f"Operación {tipo} en {simbolo}: {mensaje}")

class ErrorRiskManagement(Exception):
    """Excepción para errores en gestión de riesgo."""
    def __init__(self, motivo="", nivel_riesgo=0.0):
        self.motivo = motivo
        self.nivel_riesgo = nivel_riesgo
        super().__init__(f"Gestión de riesgo: {motivo} (riesgo: {nivel_riesgo}%)")

class ErrorEstrategia(Exception):
    """Excepción para errores en estrategias."""
    def __init__(self, estrategia="", mensaje="Error en estrategia"):
        self.estrategia = estrategia
        self.mensaje = mensaje
        super().__init__(f"Estrategia {estrategia}: {mensaje}")
