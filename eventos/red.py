"""
eventos/red.py
Deteccion de perdida/recuperacion de conexion por FLANCO y
recordatorio por TIEMPO, integrado al despachador de eventos.

- El flanco se detecta comparando el estado actual con el anterior.
- El recordatorio se evalua con marcas de tiempo dentro del ciclo
  de monitoreo (funcion revisar()).
- No usa hilos propios: el nucleo lo llama desde su ciclo.
"""
#LABORATORIO
import time
import socket

# Estado del modulo
_estado = {
    "conectado": None,       # None = aun no se sabe
    "ultimo_cambio": 0.0,    # marca de tiempo del ultimo flanco
    "ultimo_aviso": 0.0,     # marca del ultimo recordatorio
}

# Cada cuanto se recuerda que la red sigue caida (segundos)
INTERVALO_RECORDATORIO = 60.0

# Host de prueba para verificar conectividad
HOST_PRUEBA = ("8.8.8.8", 53)
TIMEOUT = 1.5


def _hay_conexion():
    """Prueba rapida de conectividad con un socket TCP."""
    try:
        with socket.create_connection(HOST_PRUEBA, timeout=TIMEOUT):
            return True
    except OSError:
        return False


def revisar():
    """
    Se llama desde nucleo.ciclo() en cada vuelta.
    Devuelve una lista de tuplas (nombre_evento, dato) para el despachador.
    """
    eventos = []
    ahora = time.time()
    hay = _hay_conexion()

    # --- Primer arranque: solo se guarda el estado, no se genera flanco ---
    if _estado["conectado"] is None:
        _estado["conectado"] = hay
        _estado["ultimo_cambio"] = ahora
        _estado["ultimo_aviso"] = ahora
        return eventos

    # --- FLANCO: cambio de estado ---
    if hay != _estado["conectado"]:
        _estado["conectado"] = hay
        _estado["ultimo_cambio"] = ahora
        _estado["ultimo_aviso"] = ahora
        if hay:
            eventos.append(("red_restaurada", {}))
        else:
            eventos.append(("red_perdida", {}))
        return eventos

    # --- TIEMPO: recordatorio si sigue caida ---
    if not hay:
        if ahora - _estado["ultimo_aviso"] >= INTERVALO_RECORDATORIO:
            _estado["ultimo_aviso"] = ahora
            segundos = int(ahora - _estado["ultimo_cambio"])
            eventos.append(("red_sin_conexion", {"segundos": segundos}))

    return eventos