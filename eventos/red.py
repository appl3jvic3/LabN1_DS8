# eventos/red.py
import threading
import time
import subprocess
import platform
import logging
from eventos import despachador
from almacenamiento import registro  # Para registrar el evento

logger = logging.getLogger(__name__)

class MonitorRed:
    """
    Monitorea la conectividad de red y genera eventos por flanco.
    """
    def __init__(self, host="8.8.8.8", intervalo=10, recordatorio=60):
        self.host = host
        self.intervalo = intervalo
        self.recordatorio = recordatorio
        self.estado_actual = True  # Asumimos que hay conexión al inicio
        self.ultimo_cambio = time.time()
        self.activo = True
        self.hilo = threading.Thread(target=self._bucle_monitoreo, daemon=True)
        self.hilo.start()
        logger.info(f"Monitor de red iniciado. Host: {host}, Intervalo: {intervalo}s")

    def _ping(self):
        """Realiza un ping al host. Devuelve True si hay respuesta."""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', self.host]
        try:
            # Ejecutamos con timeout para no bloquear mucho
            result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def _bucle_monitoreo(self):
        while self.activo:
            time.sleep(self.intervalo)
            hay_conexion = self._ping()
            ahora = time.time()

            if hay_conexion != self.estado_actual:
                # Cambio de estado (flanco)
                self.estado_actual = hay_conexion
                self.ultimo_cambio = ahora
                if hay_conexion:
                    mensaje = "Conexión de red restaurada."
                    nivel = "INFO"
                else:
                    mensaje = "Pérdida de conexión de red."
                    nivel = "ALERTA"

                # Registramos el evento. Esto disparará a todos los manejadores, incluido el sonido.
                registro.registrar_evento(nivel, "red", mensaje)
                # O también podríamos llamar directamente al despachador si quisiéramos.
                # despachador.despachar_evento(...)
                logger.info(f"Evento de red: {mensaje}")

            elif not self.estado_actual:
                # Si sigue sin conexión, verificar recordatorio
                if ahora - self.ultimo_cambio >= self.recordatorio:
                    self.ultimo_cambio = ahora
                    mensaje = "Recordatorio: Conexión de red sigue perdida."
                    registro.registrar_evento("AVISO", "red", mensaje)
                    logger.info(mensaje)

    def detener(self):
        self.activo = False
        self.hilo.join()
        logger.info("Monitor de red detenido.")

# Instancia global
monitor_red = MonitorRed()