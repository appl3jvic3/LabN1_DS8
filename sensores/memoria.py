"""
sensores/memoria.py
Uso de memoria RAM y de la memoria de intercambio (swap).

La swap es una senal digital: el sistema la usa o no la usa. Su cambio es
un evento de flanco.
"""

import psutil

ETIQUETA = "Memoria RAM"
UNIDAD = "%"

def disponible():
    return True

def leer():
    try:
        m = psutil.virtual_memory()
        s = psutil.swap_memory()
    except Exception:
        return None

    return {
        "valor": round(m.percent, 1),
        "unidad": UNIDAD,
        "porcentaje": m.percent,
        "detalle": (f"{m.used / (1024**3):.1f} GB de "
                    f"{m.total / (1024**3):.1f} GB en uso"),
        "extra": {
            "usa_swap": s.used > 0,
            "swap_pct": round(s.percent, 1),
        },
    }