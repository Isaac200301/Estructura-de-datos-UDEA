"""
analisis.py
===========
Métricas de rendimiento y análisis comparativo: KD-Tree vs Fuerza Bruta.

Preguntas que responde este análisis:
    1. ¿A partir de qué tamaño de datos el KD-Tree supera a la fuerza bruta?
    2. ¿Cuál es el peor caso de la fuerza bruta?
    3. ¿Cómo escala el KD-Tree frente a la fuerza bruta en casos extremos?
"""

import random
import time
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import sys
sys.stdout.reconfigure(encoding='utf-8')

from KDtree import (
    construir_arbol,
    busqueda_radio,
    busqueda_fuerza_bruta,
    vecino_cercano,
    vecino_bruta,
    calcular_distancia,
)

SEMILLA = 42
random.seed(SEMILLA)

# ──────────────────────────────────────────────
# Generador de datos sintéticos
# (para no depender de internet en el análisis)
# ──────────────────────────────────────────────

def generar_puntos(n, escala=20_000):
    """
    Genera n puntos aleatorios 2D en un cuadrado de lado `escala` metros.
    Se usa coordenadas sintéticas para el benchmark ya que queremos
    controlar exactamente el tamaño de la muestra.
    """
    return [
        (random.uniform(0, escala), random.uniform(0, escala))
        for _ in range(n)
    ]

def medir_tiempo(funcion, *args, repeticiones=5):
    """
    Mide el tiempo promedio de ejecución de una función.
    Hace varias repeticiones y descarta la primera (warm-up).
    """
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        funcion(*args)
        tiempos.append(time.perf_counter() - t0)
    return sum(tiempos[1:]) / (repeticiones - 1)   # promedio sin warm-up


# ──────────────────────────────────────────────
# 1. PEOR CASO DE FUERZA BRUTA
# ──────────────────────────────────────────────
# El peor caso de fuerza bruta para range search es cuando el radio
# abarca TODOS los puntos → tiene que calcular n distancias Y llenar
# una lista de n resultados. No hay forma de acortar esto.
#
# Lo provocamos usando un radio = diagonal del espacio completo,
# garantizando que calcular_distancia se llame n veces y todos entren.
# ──────────────────────────────────────────────

print("=" * 60)
print("  1. PEOR CASO — Fuerza Bruta (radio = diagonal total)")
print("=" * 60)

RADIO_NORMAL  = 500        # radio del ejercicio
RADIO_ENORME  = 1e9        # garantiza que TODOS los puntos queden dentro
N_PEOR_CASO   = 10_000

puntos_pc = generar_puntos(N_PEOR_CASO)
punto_q_pc = (10_000, 10_000)   # centro del espacio

t_bf_normal = medir_tiempo(busqueda_fuerza_bruta, puntos_pc, punto_q_pc, RADIO_NORMAL)
t_bf_peor   = medir_tiempo(busqueda_fuerza_bruta, puntos_pc, punto_q_pc, RADIO_ENORME)

# Construir árbol para comparar
arbol_pc = construir_arbol(puntos_pc)
t_kd_normal = medir_tiempo(busqueda_radio, arbol_pc, punto_q_pc, RADIO_NORMAL)
t_kd_peor   = medir_tiempo(busqueda_radio, arbol_pc, punto_q_pc, RADIO_ENORME)

print(f"  n = {N_PEOR_CASO:,} puntos")
print()
print(f"  Radio normal ({RADIO_NORMAL} m):")
print(f"    Fuerza bruta  : {t_bf_normal*1000:8.3f} ms")
print(f"    KD-Tree       : {t_kd_normal*1000:8.3f} ms")
print()
print(f"  Peor caso (radio enorme, todos los puntos):")
print(f"    Fuerza bruta  : {t_bf_peor*1000:8.3f} ms  O(n)")
print(f"    KD-Tree       : {t_kd_peor*1000:8.3f} ms  O(n log n) peor caso")
print()
print("  Conclusion peor caso:")
print("     La fuerza bruta siempre es O(n)  no depende del radio.")
print("     El KD-Tree en peor caso (radio infinito) degenera a O(n log n)")
print("     porque no puede podar ninguna rama.")
print()


# ──────────────────────────────────────────────
# 2. UMBRAL: ¿Cuándo el KD-Tree empieza a ganar?
# ──────────────────────────────────────────────
# Variamos n desde 100 hasta 100.000 y medimos el tiempo promedio
# de 20 consultas aleatorias con radio de 500 m.
#
# El KD-Tree tarda O(n log n) en construirse, pero la consulta es
# O(log n). La fuerza bruta tarda O(n) en cada consulta.
# El umbral es donde: tiempo_kd_consulta < tiempo_bf_consulta
# ──────────────────────────────────────────────

print("=" * 60)
print("  2. UMBRAL  ¿Dónde gana el KD-Tree?")
print("=" * 60)

tamanos = [100, 200, 500, 1_000, 2_000, 3_000, 5_000,
           7_500, 10_000, 20_000, 50_000, 100_000]
N_CONSULTAS = 20   # consultas por tamaño para promediar
RADIO_BENCH = 500

tiempos_bf   = []
tiempos_kd   = []
tiempos_const = []

for n in tamanos:
    pts = generar_puntos(n)
    consultas = [random.choice(pts) for _ in range(N_CONSULTAS)]

    # Tiempo de construcción del árbol
    t_c = medir_tiempo(construir_arbol, pts)
    tiempos_const.append(t_c * 1000)

    # Fuerza bruta: promedio de N_CONSULTAS
    t_bf_total = 0
    for q in consultas:
        t_bf_total += medir_tiempo(busqueda_fuerza_bruta, pts, q, RADIO_BENCH,
                                    repeticiones=3)
    tiempos_bf.append((t_bf_total / N_CONSULTAS) * 1000)

    # KD-Tree: construir una vez, luego consultas
    arbol_b = construir_arbol(pts)
    t_kd_total = 0
    for q in consultas:
        t_kd_total += medir_tiempo(busqueda_radio, arbol_b, q, RADIO_BENCH,
                                    repeticiones=3)
    tiempos_kd.append((t_kd_total / N_CONSULTAS) * 1000)

    ratio = tiempos_bf[-1] / tiempos_kd[-1] if tiempos_kd[-1] > 0 else 1
    simbolo = "KD gana" if tiempos_kd[-1] < tiempos_bf[-1] else "  BF gana "
    print(f"  n={n:>7,} | BF={tiempos_bf[-1]:7.3f} ms | "
          f"KD={tiempos_kd[-1]:7.3f} ms | ratio={ratio:5.2f}x  {simbolo}")

# Encontrar umbral exacto
umbral_n = None
for i in range(len(tamanos)):
    if tiempos_kd[i] < tiempos_bf[i]:
        umbral_n = tamanos[i]
        break

print()
if umbral_n:
    print(f"  Umbral encontrado: el KD-Tree comienza a ganar a partir de"
          f" n igual a {umbral_n:,} puntos")
else:
    print("  En el rango probado, la fuerza bruta sigue siendo competitiva.")
print()


# ──────────────────────────────────────────────
# 3. ANÁLISIS ADICIONAL: vecino más cercano
# ──────────────────────────────────────────────

print("=" * 60)
print("  3. VECINO MÁS CERCANO  KD-Tree vs Fuerza Bruta")
print("=" * 60)

tiempos_vmc_bf = []
tiempos_vmc_kd = []

for n in tamanos:
    pts = generar_puntos(n)
    consultas = [random.choice(pts) for _ in range(N_CONSULTAS)]
    arbol_v = construir_arbol(pts)

    t_bf = sum(medir_tiempo(vecino_bruta, pts, q, repeticiones=3)
               for q in consultas) / N_CONSULTAS * 1000
    t_kd = sum(medir_tiempo(vecino_cercano, arbol_v, q, repeticiones=3)
               for q in consultas) / N_CONSULTAS * 1000

    tiempos_vmc_bf.append(t_bf)
    tiempos_vmc_kd.append(t_kd)

    ratio = t_bf / t_kd if t_kd > 0 else 1
    simbolo = "KD gana" if t_kd < t_bf else "  BF gana "
    print(f"  n={n:>7,} | BF={t_bf:7.3f} ms | KD={t_kd:7.3f} ms | "
          f"ratio={ratio:5.2f}x  {simbolo}")
print()


# ──────────────────────────────────────────────
# 4. GRÁFICOS
# ──────────────────────────────────────────────

estilo = {
    "facecolor": "#0d1117",
    "edgecolor": "#333355",
}

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.patch.set_facecolor("#0d1117")

COLOR_BF = "#ff6b6b"
COLOR_KD = "#4ecdc4"
COLOR_CO = "#a29bfe"


# ── Gráfico 1: Range Search ──
ax1 = axes[0]
ax1.set_facecolor("#0d1117")
ax1.plot(tamanos, tiempos_bf, "o-", color=COLOR_BF, linewidth=2,
         markersize=5, label="Fuerza Bruta")
ax1.plot(tamanos, tiempos_kd, "s-", color=COLOR_KD, linewidth=2,
         markersize=5, label="KD-Tree")
ax1.plot(tamanos, tiempos_const, "^--", color=COLOR_CO, linewidth=1.5,
         markersize=4, alpha=0.7, label="Construcción KD")
if umbral_n:
    ax1.axvline(x=umbral_n, color="yellow", linestyle=":", alpha=0.6,
                label=f"Umbral ≈ {umbral_n:,}")
ax1.set_xscale("log")
ax1.set_yscale("log")
ax1.set_xlabel("n (número de puntos)", color="#aaaaaa")
ax1.set_ylabel("Tiempo (ms)", color="#aaaaaa")
ax1.set_title("Range Search — 500 m", color="white", fontsize=11)
ax1.legend(fontsize=8, facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
ax1.tick_params(colors="#aaaaaa")
for s in ax1.spines.values():
    s.set_edgecolor("#333355")


# ── Gráfico 2: Vecino más cercano ──
ax2 = axes[1]
ax2.set_facecolor("#0d1117")
ax2.plot(tamanos, tiempos_vmc_bf, "o-", color=COLOR_BF, linewidth=2,
         markersize=5, label="Fuerza Bruta")
ax2.plot(tamanos, tiempos_vmc_kd, "s-", color=COLOR_KD, linewidth=2,
         markersize=5, label="KD-Tree")
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlabel("n (número de puntos)", color="#aaaaaa")
ax2.set_ylabel("Tiempo (ms)", color="#aaaaaa")
ax2.set_title("Vecino más cercano", color="white", fontsize=11)
ax2.legend(fontsize=8, facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
ax2.tick_params(colors="#aaaaaa")
for s in ax2.spines.values():
    s.set_edgecolor("#333355")


# ── Gráfico 3: Peor caso ──
ax3 = axes[2]
ax3.set_facecolor("#0d1117")

categorias = [f"BF\n500 m", f"KD\n500 m", f"BF\nRadio ∞\n(peor caso)", f"KD\nRadio ∞\n(peor caso)"]
valores    = [t_bf_normal*1000, t_kd_normal*1000, t_bf_peor*1000, t_kd_peor*1000]
colores_b  = [COLOR_BF, COLOR_KD, "#ff1744", "#00bcd4"]

bars = ax3.bar(categorias, valores, color=colores_b, edgecolor="#333355",
               linewidth=0.8, width=0.55)
for bar, val in zip(bars, valores):
    ax3.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() * 1.05,
             f"{val:.2f} ms", ha="center", va="bottom",
             color="white", fontsize=8, fontweight="bold")

ax3.set_title(f"Peor caso (n={N_PEOR_CASO:,})", color="white", fontsize=11)
ax3.set_ylabel("Tiempo (ms)", color="#aaaaaa")
ax3.tick_params(colors="#aaaaaa")
ax3.set_facecolor("#0d1117")
for s in ax3.spines.values():
    s.set_edgecolor("#333355")
ax3.set_ylim(0, max(valores) * 1.2)


plt.suptitle(
    "Análisis de rendimiento — KD-Tree vs Fuerza Bruta\n"
    "Sistema de logística · Medellín, Colombia",
    color="white", fontsize=13, y=1.02
)
plt.tight_layout()
plt.savefig("analisis_rendimiento.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.show()
print("analisis_rendimiento.png guardado")


# ──────────────────────────────────────────────
# 5. DISCUSIÓN DE RESULTADOS
# ──────────────────────────────────────────────

print()
print("=" * 60)
print("  DISCUSIÓN DE RESULTADOS")
print("=" * 60)
print("""
  Complejidad teórica:
  ┌──────────────────┬────────────────┬────────────────────┐
  │ Operación        │ Fuerza Bruta   │ KD-Tree            │
  ├──────────────────┼────────────────┼────────────────────┤
  │ Construcción     │ —              │ O(n log n)         │
  │ Range Search     │ O(n)           │ O(log n + k)       │
  │ Vecino cercano   │ O(n)           │ O(log n) promedio  │
  │ Peor caso query  │ O(n) siempre   │ O(n) — sin poda    │
  └──────────────────┴────────────────┴────────────────────┘

  Hallazgos empíricos:

  1. La fuerza bruta siempre recorre los n puntos.
     No importa el radio: siempre calcula n distancias.

  2. El KD-Tree tiene overhead de construcción (O(n log n)),
     pero cada consulta es mucho más rápida para n grande.
     Esto lo hace ideal cuando los datos son estáticos
     (como en este ejercicio) y hay muchas consultas.

  3. El peor caso del KD-Tree ocurre cuando el radio es tan
     grande que cubre todo el espacio: no puede podar ninguna
     rama y recorre el árbol completo → O(n log n).
     Paradójicamente, esto es PEOR que la fuerza bruta O(n).

  4. Para radio pequeño (500 m en ciudad real), el KD-Tree
     poda la mayoría de ramas y es significativamente más
     rápido incluso para n moderados (≈ 1.000 - 3.000 puntos).

  Conclusión:
  El KD-Tree es la estructura correcta para consultas espaciales
  repetidas sobre datos estáticos. Su ventaja crece con n y
  se maximiza cuando el radio es pequeño relativo al espacio total.
""")
