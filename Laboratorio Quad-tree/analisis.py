"""
analisis.py
===========
Metricas de rendimiento y analisis comparativo: Quadtree vs Fuerza Bruta.

Preguntas que responde este analisis:
    1. Para que tamano de datos el Quadtree comienza a ser mas rapido que fuerza bruta?
    2. Cual es el peor caso de la fuerza bruta?
    3. Como escala el Quadtree frente a la fuerza bruta en casos extremos?

Nota sobre el peor caso del Quadtree:
    A diferencia del KD-Tree, el Quadtree guarda varios puntos por hoja (capacidad=4).
    Con radio infinito, visita todos los nodos (~n/cap nodos hoja) pero con overhead
    de la recursion sobre 4 hijos por nodo. Esto lo hace O(n) pero mas lento que
    la fuerza bruta O(n) pura por el overhead de la estructura del arbol.
"""

"""

Comparacion: Quadtree vs Fuerza Bruta

Que queremos ver:
1. Cuando empieza a ganar el Quadtree
2. Que pasa en el peor caso
3. Como se comporta el vecino mas cercano
"""

import random
import time
import matplotlib.pyplot as plt

from Quadtree import (
    construir_quadtree,
    busqueda_radio,
    busqueda_fuerza_bruta,
    vecino_cercano,
    vecino_bruta,
)

# -----------------------------
# CONFIG
# -----------------------------
random.seed(42)

RADIO = 500
RADIO_GRANDE = 1e9

tamanos = [100, 500, 1000, 5000, 10000]


# -----------------------------
# GENERAR DATOS
# -----------------------------
def generar_puntos(n):
    return [(random.uniform(0, 20000), random.uniform(0, 20000)) for _ in range(n)]


def medir(func, *args):
    t0 = time.perf_counter()
    res = func(*args)
    t1 = time.perf_counter()
    return t1 - t0, res


# -----------------------------
# LISTAS DE RESULTADOS
# -----------------------------
tiempos_bf = []
tiempos_qt = []
tiempos_const = []

tiempos_bf_v = []
tiempos_qt_v = []


# -----------------------------
# BENCHMARK
# -----------------------------
for n in tamanos:
    print(f"\nProbando n = {n}")

    puntos = generar_puntos(n)
    consultas = random.sample(puntos, min(10, len(puntos)))

    # -------- Construcción --------
    t_const, arbol = medir(construir_quadtree, puntos)
    tiempos_const.append(t_const * 1000)

    # -------- Range search --------
    t_bf_total = 0
    t_qt_total = 0

    for q in consultas:
        t_bf, _ = medir(busqueda_fuerza_bruta, puntos, q, RADIO)
        t_qt, _ = medir(busqueda_radio, arbol, q, RADIO)

        t_bf_total += t_bf
        t_qt_total += t_qt

    tiempos_bf.append((t_bf_total / len(consultas)) * 1000)
    tiempos_qt.append((t_qt_total / len(consultas)) * 1000)

    # -------- Vecino cercano --------
    t_bf_total = 0
    t_qt_total = 0

    for q in consultas:
        t_bf, _ = medir(vecino_bruta, puntos, q)
        t_qt, _ = medir(vecino_cercano, arbol, q)

        t_bf_total += t_bf
        t_qt_total += t_qt

    tiempos_bf_v.append((t_bf_total / len(consultas)) * 1000)
    tiempos_qt_v.append((t_qt_total / len(consultas)) * 1000)


# -----------------------------
# PEOR CASO
# -----------------------------
print("\nProbando peor caso...")

puntos = generar_puntos(10000)
q = (10000, 10000)

t_bf_normal, _ = medir(busqueda_fuerza_bruta, puntos, q, RADIO)
t_bf_peor, _ = medir(busqueda_fuerza_bruta, puntos, q, RADIO_GRANDE)

_, arbol = medir(construir_quadtree, puntos)

t_qt_normal, _ = medir(busqueda_radio, arbol, q, RADIO)
t_qt_peor, _ = medir(busqueda_radio, arbol, q, RADIO_GRANDE)


# -----------------------------
# GRAFICAS
# -----------------------------

COLOR_BF = "#495057"   # gris
COLOR_QT = "#1c7ed6"   # azul
COLOR_CONST = "#adb5bd"

fig, ax = plt.subplots(1, 3, figsize=(15, 5))

# -----------------------------
# 1. Range search + construccion
# -----------------------------
ax[0].plot(tamanos, tiempos_bf, "o-", color=COLOR_BF, label="Fuerza bruta")
ax[0].plot(tamanos, tiempos_qt, "s-", color=COLOR_QT, label="Quadtree")
ax[0].plot(tamanos, tiempos_const, "^-", color=COLOR_CONST, label="Construccion QT")

ax[0].set_title("Busqueda por radio")
ax[0].set_xlabel("n")
ax[0].set_ylabel("Tiempo (ms)")
ax[0].legend()

# -----------------------------
# 2. Vecino mas cercano
# -----------------------------
ax[1].plot(tamanos, tiempos_bf_v, "o-", color=COLOR_BF, label="Fuerza bruta")
ax[1].plot(tamanos, tiempos_qt_v, "s-", color=COLOR_QT, label="Quadtree")

ax[1].set_title("Vecino mas cercano")
ax[1].set_xlabel("n")
ax[1].set_ylabel("Tiempo (ms)")
ax[1].legend()

# -----------------------------
# 3. Peor caso
# -----------------------------
categorias = ["BF normal", "QT normal", "BF peor", "QT peor"]
valores = [
    t_bf_normal*1000,
    t_qt_normal*1000,
    t_bf_peor*1000,
    t_qt_peor*1000
]

colores = [COLOR_BF, COLOR_QT, "#868e96", "#339af0"]

ax[2].bar(categorias, valores, color=colores)
ax[2].set_title("Peor caso")
ax[2].set_ylabel("Tiempo (ms)")

# -----------------------------
plt.tight_layout()
plt.savefig("analisis.png")
plt.show()
