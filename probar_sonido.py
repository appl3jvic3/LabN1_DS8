"""
Prueba aislada del reproductor de alertas.
NO arranca el monitor. Solo verifica que suenan los WAV.
"""
import time
from eventos.alertas import reproductor, SONIDOS

print("Archivos configurados:")
for clave, ruta in SONIDOS.items():
    import os
    estado = "OK" if os.path.exists(ruta) else "FALTA"
    print(f"  {clave:<25} {ruta}  [{estado}]")

print("\nReproduciendo cada sonido (1 por segundo)...")
for clave in SONIDOS:
    print(f"  -> {clave}")
    reproductor.reproducir(clave)
    time.sleep(1.2)

print("\nPrueba de anti-rebote: 5 llamadas seguidas a 'default'.")
print("Solo debe sonar UNA vez.")
for _ in range(5):
    reproductor.reproducir("default")
    time.sleep(0.2)

time.sleep(2)
print("\nListo. Si escuchaste tonos distintos, el reproductor funciona.")