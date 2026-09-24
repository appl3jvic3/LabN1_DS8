# eventos/alertas.py
import threading
import queue
import time
import os
import platform
import logging
import pygame

logger = logging.getLogger(__name__)

# Intentamos importar pygame para una reproducción de audio robusta
try:
    pygame.init()
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame no está instalado. Las alertas sonoras usarán el sistema.")

# Definimos los sonidos. Los archivos deben existir en una carpeta 'sonidos'.
# Por ejemplo: 'sonidos/alerta_cpu.wav', 'sonidos/alerta_red.wav'
SONIDOS = {
    "cpu_alto": "sonidos/alerta_cpu.wav",
    "ram_alta": "sonidos/alerta_ram.wav",
    "disco_lleno": "sonidos/alerta_disco.wav",
    "red_pico": "sonidos/alerta_red.wav",
    "red_perdida": "sonidos/alerta_red_perdida.wav",
    "red_restaurada": "sonidos/alerta_red_restaurada.wav",
    "default": "sonidos/alerta_default.wav",
}

class ReproductorAlertas:
    """
    Reproductor de alertas sonoras no bloqueante.
    Utiliza una cola y un hilo para reproducir sonidos en segundo plano.
    """
    def __init__(self):
        self.cola = queue.Queue()
        self.activo = True
        self.hilo = threading.Thread(target=self._bucle_reproduccion, daemon=True)
        self.hilo.start()
        logger.info("Reproductor de alertas iniciado.")

    def _bucle_reproduccion(self):
        while self.activo:
            try:
                # Espera hasta 1 segundo para evitar un bucle ocupado
                sonido, evento = self.cola.get(timeout=1)
                if sonido:
                    self._reproducir_sonido(sonido)
                self.cola.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error en el reproductor de alertas: {e}")

    def _reproducir_sonido(self, archivo_sonido):
        """Reproduce un archivo de sonido usando el mejor método disponible."""
        if PYGAME_AVAILABLE:
            try:
                # Detenemos cualquier sonido anterior para evitar superposición
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.music.load(archivo_sonido)
                pygame.mixer.music.play()
                # Esperamos a que termine, pero esto ocurre en el hilo, así que no bloquea el ciclo principal
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                return
            except Exception as e:
                logger.error(f"Error reproduciendo sonido con pygame: {e}")

        # Fallback si pygame no está disponible o falla
        sistema = platform.system()
        if sistema == "Windows":
            try:
                import winsound
                winsound.PlaySound(archivo_sonido, winsound.SND_FILENAME)
            except Exception as e:
                logger.error(f"Error reproduciendo sonido en Windows: {e}")
        elif sistema == "Darwin":  # macOS
            os.system(f"afplay {archivo_sonido} &")
        elif sistema == "Linux":
            os.system(f"aplay {archivo_sonido} &")
        else:
            # Como último recurso, intentamos el beep del sistema
            print("\a")

    def reproducir(self, clave_sonido, evento=None):
        """
        Añade una alerta sonora a la cola para su reproducción.
        No bloquea.
        """
        archivo = SONIDOS.get(clave_sonido, SONIDOS["default"])
        if not os.path.exists(archivo):
            logger.warning(f"Archivo de sonido no encontrado: {archivo}. Usando beep.")
            archivo = None
        self.cola.put((archivo, evento))
        logger.debug(f"Alerta sonora encolada: {clave_sonido}")

    def detener(self):
        self.activo = False
        self.hilo.join()
        logger.info("Reproductor de alertas detenido.")

# Instancia global para ser usada por los manejadores
reproductor = ReproductorAlertas()