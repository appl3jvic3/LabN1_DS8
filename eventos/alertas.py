"""
eventos/alertas.py
Reproductor de alertas sonoras NO bloqueante.

- Usa una deque como cola de reproduccion (no queue.Queue).
- Usa marcas de tiempo para:
    * evitar repetir el mismo sonido antes de un intervalo minimo
    * no encolar sonidos viejos (caducidad)
- Un hilo demonio consume la cola; el ciclo de monitoreo nunca se bloquea.
"""

import threading
import time
from collections import deque # LABORATORIO
import os
import platform

# LABORATORIO
SONIDOS = {
    "cpu_alta":        "sonidos/alerta_cpu.wav",
    "ram_alta":        "sonidos/alerta_ram.wav",
    "disco_lleno":     "sonidos/alerta_disco.wav",
    "red_pico":        "sonidos/alerta_red.wav",
    "red_perdida":     "sonidos/alerta_red_perdida.wav",
    "red_restaurada":  "sonidos/alerta_red_restaurada.wav",
    "default":         "sonidos/alerta_default.wav",
}

# No repetir el mismo sonido antes de REPETIR_MIN segundos.
REPETIR_MIN = 5.0

# Un sonido encolado caduca si no se reproduce en CADUCIDAD segundos.
CADUCIDAD = 10.0

# LABORATORIO

class ReproductorAlertas:
    """
    Cola no bloqueante de alertas sonoras.
    Cada elemento de la cola es una tupla (clave, archivo, marca_tiempo).
    """

    def __init__(self):
        self.cola = deque()               # cola doble: append por la derecha
        self.lock = threading.Lock()      # protege la deque entre hilos
        self.activo = True
        self.ultimo_sonido = {}           # clave -> marca de tiempo
        self.hilo = threading.Thread(target=self._bucle, daemon=True)
        self.hilo.start()

    # --- API publica ---------------------------------------------------------
    def reproducir(self, clave, evento=None):
        """Encola un sonido. NO bloquea. Ignora repeticiones muy seguidas."""
        ahora = time.time()

        # Anti-rebote por marca de tiempo: no repetir el mismo sonido.
        ultimo = self.ultimo_sonido.get(clave, 0.0)
        if ahora - ultimo < REPETIR_MIN:
            return
        self.ultimo_sonido[clave] = ahora

        archivo = SONIDOS.get(clave, SONIDOS["default"])
        if not os.path.exists(archivo):
            archivo = None  # se usara beep del sistema

        with self.lock:
            self.cola.append((clave, archivo, ahora))

    def detener(self):
        self.activo = False
        self.hilo.join(timeout=2)

    # --- Bucle del hilo consumidor ------------------------------------------
    def _bucle(self):
        while self.activo:
            item = None
            with self.lock:
                if self.cola:
                    item = self.cola.popleft()
            if item is None:
                time.sleep(0.1)
                continue

            clave, archivo, marca = item

            # Marca de tiempo: descartar sonidos caducados.
            if time.time() - marca > CADUCIDAD:
                continue

            try:
                self._reproducir(archivo)
            except Exception:
                pass

    def _reproducir(self, archivo):
        if archivo is None:
            print("\a")
            return
        sistema = platform.system()
        if sistema == "Windows":
            try:
                import winsound
                winsound.PlaySound(archivo, winsound.SND_FILENAME)
            except Exception:
                print("\a")
        elif sistema == "Darwin":
            os.system(f"afplay {archivo} >/dev/null 2>&1 &")
        else:
            os.system(f"aplay {archivo} >/dev/null 2>&1 &")


reproductor = ReproductorAlertas()
#LABORATORIO