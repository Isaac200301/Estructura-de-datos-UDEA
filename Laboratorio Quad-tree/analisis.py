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

import random
import time
import matplotlib.pyplot as plt
import sys
sys.stdout.reconfigure(encoding="utf-8")

from Quadtree import (
    construir_quadtree,
    busqueda_radio,
    busqueda_fuerza_bruta,
    vecino_cercano,
    vecino_bruta,
    calcular_distancia,
)

SEMILLA = 42
random.seed(SEMILLA)


# ─────────────────────────────────────────────────────────
# Generador de datos sinteticos
# ─────────────────────────────────────────────────────────

def generar_puntos(n, escala=20_000):
    """
    Genera n puntos 2D en un cuadrado de lado `escala` metros.
    Datos sinteticos para controlar exactamente el tamano del benchmark.
    """
    return [
        (random.uniform(0, escala), random.uniform(0, escala))
        for _ in range(n)
    ]


def medir_tiempo(funcion, *args, repeticiones=5):
    """
    Tiempo promedio de ejecucion (descarta la primera repeticion como warm-up).
    """
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        funcion(*args)
        tiempos.append(time.perf_counter() - t0)
    return sum(tiempos[1:]) / (repeticiones - 1)


# ─────────────────────────────────────────────────────────
# 1. PEOR CASO DE FUERZA BRUTA
# ─────────────────────────────────────────────────────────
# El peor caso de fuerza bruta para range search ocurre cuando el radio
# es tan grande que TODOS los puntos estan dentro.
# → calcula n distancias Y llena una lista de n resultados.
#
# Con radio normal (500 m) solo evalua los puntos cercanos,
# pero igual recorre toda la lista (no puede saltar ninguno).
# ─────────────────────────────────────────────────────────

print("=" * 60)
print("  1. PEOR CASO — Fuerza Bruta (radio = infinito)")
print("=" * 60)

RADIO_NORMAL = 500
RADIO_ENORME = 1e9        # garantiza que TODOS los puntos queden dentro
N_PEOR_CASO  = 10_000

puntos_pc  = generar_puntos(N_PEOR_CASO)
punto_q_pc = (10_000, 10_000)

t_bf_normal = medir_tiempo(busqueda_fuerza_bruta, puntos_pc, punto_q_pc, RADIO_NORMAL)
t_bf_peor   = medir_tiempo(busqueda_fuerza_bruta, puntos_pc, punto_q_pc, RADIO_ENORME)

arbol_pc    = construir_quadtree(puntos_pc)
t_qt_normal = medir_tiempo(busqueda_radio, arbol_pc, punto_q_pc, RADIO_NORMAL)
t_qt_peor   = medir_tiempo(busqueda_radio, arbol_pc, punto_q_pc, RADIO_ENORME)

print(f"  n = {N_PEOR_CASO:,} puntos")
print()
print(f"  Radio normal ({RADIO_NORMAL} m):")
print(f"    Fuerza bruta : {t_bf_normal*1000:8.3f} ms")
print(f"    Quadtree     : {t_qt_normal*1000:8.3f} ms")
print()
print(f"  Peor caso (radio infinito, todos los puntos dentro):")
print(f"    Fuerza bruta : {t_bf_peor*1000:8.3f} ms  <- O(n) puro")
print(f"    Quadtree     : {t_qt_peor*1000:8.3f} ms  <- O(n) con overhead del arbol")
print()
print("  Conclusion peor caso:")
print("     Ambos son O(n) con radio infinito, pero el Quadtree es mas lento")
print("     porque tiene overhead de visitar nodos internos del arbol (4 hijos c/u).")
print("     La fuerza bruta gana en el peor caso por tener la constante mas baja.")
print()


# ─────────────────────────────────────────────────────────
# 2. UMBRAL: para que tamano gana el Quadtree?
# ─────────────────────────────────────────────────────────
# Variamos n de 100 a 100.000 y medimos el promedio de 20 consultas
# con radio de 500 m. Buscamos el punto donde:
#     tiempo_quadtree < tiempo_fuerza_bruta
# ─────────────────────────────────────────────────────────

print("=" * 60)
print("  2. UMBRAL  Para que n gana el Quadtree?")
print("=" * 60)

tamanos = [100, 200, 500, 1_000, 2_000, 3_000, 5_000,
           7_500, 10_000, 20_000, 50_000, 100_000]
N_CONSULTAS = 20
RADIO_BENCH = 500

tiempos_bf    = []
tiempos_qt    = []
tiempos_const = []

for n in tamanos:
    pts      = generar_puntos(n)
    consultas = [random.choice(pts) for _ in range(N_CONSULTAS)]

    # Construccion del arbol (se hace una sola vez)
    t_c = medir_tiempo(construir_quadtree, pts)
    tiempos_const.append(t_c * 1000)

    # Fuerza bruta: promedio de N_CONSULTAS
    t_bf_total = 0
    for q in consultas:
        t_bf_total += medir_tiempo(busqueda_fuerza_bruta, pts, q, RADIO_BENCH,
                                   repeticiones=3)
    tiempos_bf.append((t_bf_total / N_CONSULTAS) * 1000)

    # Quadtree: construir una vez, luego consultas
    arbol_b = construir_quadtree(pts)
    t_qt_total = 0
    for q in consultas:
        t_qt_total += medir_tiempo(busqueda_radio, arbol_b, q, RADIO_BENCH,
                                   repeticiones=3)
    tiempos_qt.append((t_qt_total / N_CONSULTAS) * 1000)

    ratio   = tiempos_bf[-1] / tiempos_qt[-1] if tiempos_qt[-1] > 0 else 1
    simbolo = "QT gana" if tiempos_qt[-1] < tiempos_bf[-1] else "  BF gana"
    print(f"  n={n:>7,} | BF={tiempos_bf[-1]:7.3f} ms | "
          f"QT={tiempos_qt[-1]:7.3f} ms | ratio={ratio:5.2f}x  {simbolo}")

# Encontrar umbral
umbral_n = None
for i in range(len(tamanos)):
    if tiempos_qt[i] < tiempos_bf[i]:
        umbral_n = tamanos[i]
        break

print()
if umbral_n:
    print(f"  Umbral encontrado: el Quadtree gana a partir de n = {umbral_n:,} puntos")
else:
    print("  En el rango probado, la fuerza bruta sigue siendo competitiva.")
print()


# ─────────────────────────────────────────────────────────
# 3. VECINO MÁS CERCANO — Quadtree vs Fuerza Bruta
# ─────────────────────────────────────────────────────────

print("=" * 60)
print("  3. VECINO MAS CERCANO  Quadtree vs Fuerza Bruta")
print("=" * 60)

tiempos_vmc_bf = []
tiempos_vmc_qt = []

for n in tamanos:
    pts      = generar_puntos(n)
    consultas = [random.choice(pts) for _ in range(N_CONSULTAS)]
    arbol_v  = construir_quadtree(pts)

    t_bf = sum(medir_tiempo(vecino_bruta, pts, q, repeticiones=3)
               for q in consultas) / N_CONSULTAS * 1000
    t_qt = sum(medir_tiempo(vecino_cercano, arbol_v, q, repeticiones=3)
               for q in consultas) / N_CONSULTAS * 1000

    tiempos_vmc_bf.append(t_bf)
    tiempos_vmc_qt.append(t_qt)

    ratio   = t_bf / t_qt if t_qt > 0 else 1
    simbolo = "QT gana" if t_qt < t_bf else "  BF gana"
    print(f"  n={n:>7,} | BF={t_bf:7.3f} ms | QT={t_qt:7.3f} ms | "
          f"ratio={ratio:5.2f}x  {simbolo}")
print()


# ─────────────────────────────────────────────────────────
# 4. GRÁFICOS
# ─────────────────────────────────────────────────────────

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.patch.set_facecolor("#0d1117")

COLOR_BF = "#ff6b6b"
COLOR_QT = "#f9ca24"   # amarillo dorado — distinto al verde del KD-Tree
COLOR_CO = "#a29bfe"


# Grafico 1: Range Search
ax1 = axes[0]
ax1.set_facecolor("#0d1117")
ax1.plot(tamanos, tiempos_bf, "o-", color=COLOR_BF, lw=2, ms=5, label="Fuerza Bruta")
ax1.plot(tamanos, tiempos_qt, "s-", color=COLOR_QT, lw=2, ms=5, label="Quadtree")
ax1.plot(tamanos, tiempos_const, "^--", color=COLOR_CO, lw=1.5, ms=4,
         alpha=0.7, label="Construccion QT")
if umbral_n:
    ax1.axvline(x=umbral_n, color="white", ls=":", alpha=0.5,
                label=f"Umbral aprox. {umbral_n:,}")
ax1.set_xscale("log")
ax1.set_yscale("log")
ax1.set_xlabel("n (numero de puntos)", color="#aaaaaa")
ax1.set_ylabel("Tiempo (ms)", color="#aaaaaa")
ax1.set_title("Range Search — radio 500 m", color="white", fontsize=11)
ax1.legend(fontsize=8, facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
ax1.tick_params(colors="#aaaaaa")
for s in ax1.spines.values():
    s.set_edgecolor("#333355")


# Grafico 2: Vecino mas cercano
ax2 = axes[1]
ax2.set_facecolor("#0d1117")
ax2.plot(tamanos, tiempos_vmc_bf, "o-", color=COLOR_BF, lw=2, ms=5, label="Fuerza Bruta")
ax2.plot(tamanos, tiempos_vmc_qt, "s-", color=COLOR_QT, lw=2, ms=5, label="Quadtree")
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlabel("n (numero de puntos)", color="#aaaaaa")
ax2.set_ylabel("Tiempo (ms)", color="#aaaaaa")
ax2.set_title("Vecino mas cercano", color="white", fontsize=11)
ax2.legend(fontsize=8, facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
ax2.tick_params(colors="#aaaaaa")
for s in ax2.spines.values():
    s.set_edgecolor("#333355")


# Grafico 3: Peor caso (barras comparativas)
ax3 = axes[2]
ax3.set_facecolor("#0d1117")

categorias = ["BF\n500 m", "QT\n500 m",
              "BF\nRadio infinito\n(peor caso)", "QT\nRadio infinito\n(peor caso)"]
valores    = [t_bf_normal*1000, t_qt_normal*1000, t_bf_peor*1000, t_qt_peor*1000]
colores_b  = [COLOR_BF, COLOR_QT, "#ff1744", "#f0932b"]

bars = ax3.bar(categorias, valores, color=colores_b,
               edgecolor="#333355", lw=0.8, width=0.55)
for bar, val in zip(bars, valores):
    ax3.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() * 1.05,
             f"{val:.2f} ms", ha="center", va="bottom",
             color="white", fontsize=8, fontweight="bold")

ax3.set_title(f"Peor caso (n={N_PEOR_CASO:,})", color="white", fontsize=11)
ax3.set_ylabel("Tiempo (ms)", color="#aaaaaa")
ax3.tick_params(colors="#aaaaaa")
for s in ax3.spines.values():
    s.set_edgecolor("#333355")
ax3.set_ylim(0, max(valores) * 1.2)

plt.suptitle(
    "Analisis de rendimiento — Quadtree vs Fuerza Bruta\n"
    "Sistema de logistica - Medellin, Colombia",
    color="white", fontsize=13, y=1.02
)
plt.tight_layout()
plt.savefig("analisis_rendimiento.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.show()
print("analisis_rendimiento.png guardado")


# ─────────────────────────────────────────────────────────
# 5. DISCUSIÓN DE RESULTADOS
# ─────────────────────────────────────────────────────────

print()
print("=" * 60)
print("  DISCUSION DE RESULTADOS")
print("=" * 60)
print(f"""
  Complejidad teorica:
  +------------------+----------------+--------------------+
  | Operacion        | Fuerza Bruta   | Quadtree           |
  +------------------+----------------+--------------------+
  | Construccion     | --             | O(n log n)         |
  | Range Search     | O(n)           | O(log n + k)       |
  | Vecino cercano   | O(n)           | O(log n) promedio  |
  | Peor caso query  | O(n) siempre   | O(n) + overhead    |
  +------------------+----------------+--------------------+
  donde k = puntos encontrados dentro del radio

  Diferencias clave frente al KD-Tree:
  - El Quadtree divide siempre en 4 cuadrantes iguales (geometrico)
  - El KD-Tree divide por la mediana (estadistico)
  - El Quadtree funciona bien cuando los datos estan distribuidos
    de forma relativamente uniforme en el espacio
  - En zonas muy densas el Quadtree profundiza mas (mas niveles)
  - La capacidad por nodo (4 en este ejercicio) es un parametro
    que afecta el rendimiento: mas grande = arbol menos profundo
    pero mas comparaciones por nodo

  Hallazgos empiricos:

  1. La fuerza bruta siempre recorre los n puntos.
     No importa el radio: calcula n distancias sin excepcion.

  2. El Quadtree con radio 500 m puede podar la mayoria de los
     4 subarboles en cada nodo → muy rapido para consultas locales.

  3. En el peor caso (radio infinito), ambos son O(n) pero el
     Quadtree tiene overhead de visitar nodos internos (4 hijos c/u),
     lo que lo hace mas lento que la fuerza bruta O(n) puro.

  4. El umbral de ventaja del Quadtree es de aprox. {umbral_n or "N/A"} puntos
     con radio 500 m. Para n menor, el overhead de construccion
     y traversal del arbol no vale la pena.

  Conclusion:
  El Quadtree es ideal para consultas espaciales repetidas sobre
  datos estaticos con radio pequeno relativo al espacio total.
  Su ventaja visual (rectangulos anidados) lo hace intuitivo para
  entender como se organiza el espacio en zonas de distinta densidad.
""")
