"""
test.py
=======
Pruebas unitarias, visualizaciones y análisis del KD-Tree.

Incluye:
    - Verificación de correctitud (KD-Tree vs fuerza bruta)
    - Múltiples puntos de consulta con radio fijo de 500 m
    - Visualización global con líneas del árbol
    - Zoom al radio de cada punto de consulta
    - Conexiones entre el punto y sus vecinos encontrados
"""

import sys
import os
import random
import math
import pyproj
import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

# Importar nuestro módulo
from KDtree import (
    construir_arbol,
    busqueda_radio,
    vecino_cercano,
    busqueda_fuerza_bruta,
    calcular_distancia,
    NodoKD,
)

# ──────────────────────────────────────────────
# 1. CARGA Y PROYECCIÓN DE DATOS
# ──────────────────────────────────────────────

CIUDAD = "Medellin, Colombia"
RADIO_METROS = 500          # radio fijo para todas las pruebas
SEMILLA = 42
random.seed(SEMILLA)

print("=" * 55)
print("  Cargando datos de OpenStreetMap...")
print("=" * 55)

datos_geo = ox.features_from_place(CIUDAD, tags={"building": True})
datos_geo["centroide"] = datos_geo.geometry.centroid

lista_latlon = [
    (p.y, p.x)
    for p in datos_geo["centroide"]
    if p is not None
]

lista_latlon = random.sample(lista_latlon, min(10_000, len(lista_latlon)))
print(f"  Puntos cargados: {len(lista_latlon):,}")

# Proyectar a metros (EPSG:3116 — Colombia)
transformador = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3116", always_xy=True)

puntos = [
    transformador.transform(lon, lat)
    for lat, lon in lista_latlon
]
puntos = [tuple(p) for p in puntos]   # lista de (x_m, y_m)

print(f"  Proyección: EPSG:3116 (metros)")
print(f"  Dimensiones: {len(puntos[0])}D\n")


# ──────────────────────────────────────────────
# 2. CONSTRUCCIÓN DEL ÁRBOL
# ──────────────────────────────────────────────

print("Construyendo KD-Tree...")
arbol = construir_arbol(puntos)
print(" Árbol construido correctamente\n")


# ──────────────────────────────────────────────
# 3. PRUEBAS UNITARIAS
# ──────────────────────────────────────────────

print("=" * 55)
print("  PRUEBAS UNITARIAS")
print("=" * 55)

def test_distancia_2d():
    assert abs(calcular_distancia((0, 0), (3, 4)) - 5.0) < 1e-9
    assert calcular_distancia((1, 1), (1, 1)) == 0.0
    print("  test_distancia_2d")

def test_distancia_kd():
    # En 3D: sqrt(1+4+9) = sqrt(14)
    d = calcular_distancia((0, 0, 0), (1, 2, 3))
    assert abs(d - math.sqrt(14)) < 1e-9
    print("  test_distancia_kd  (3 dimensiones)")

def test_arbol_un_punto():
    arbol_mini = construir_arbol([(1.0, 2.0)])
    assert arbol_mini is not None
    assert arbol_mini.punto == (1.0, 2.0)
    print("  test_arbol_un_punto")

def test_arbol_vacio():
    assert construir_arbol([]) is None
    print(" test_arbol_vacio")

def test_busqueda_radio_correctitud():
    """KD-Tree debe devolver exactamente los mismos puntos que fuerza bruta."""
    muestra = random.sample(puntos, 200)
    punto_consulta = random.choice(puntos)
    radio_prueba = RADIO_METROS

    arbol_mini = construir_arbol(muestra)
    resultado_kd = set(busqueda_radio(arbol_mini, punto_consulta, radio_prueba))
    resultado_bf = set(busqueda_fuerza_bruta(muestra, punto_consulta, radio_prueba))

    assert resultado_kd == resultado_bf, (
        f"Diferencia entre KD ({len(resultado_kd)}) y "
        f"fuerza bruta ({len(resultado_bf)})"
    )
    print(f"  test_busqueda_radio_correctitud  ({len(resultado_kd)} puntos encontrados)")

def test_vecino_cercano_correctitud():
    """El vecino encontrado por el árbol debe coincidir con fuerza bruta."""
    muestra = random.sample(puntos, 500)
    punto_consulta = (
        random.uniform(min(p[0] for p in muestra), max(p[0] for p in muestra)),
        random.uniform(min(p[1] for p in muestra), max(p[1] for p in muestra)),
    )
    arbol_mini = construir_arbol(muestra)

    mejor_kd, dist_kd = vecino_cercano(arbol_mini, punto_consulta)
    mejor_bf, dist_bf = min(
        ((p, calcular_distancia(p, punto_consulta)) for p in muestra),
        key=lambda x: x[1],
    )
    assert abs(dist_kd - dist_bf) < 1e-6, (
        f"Distancias distintas: KD={dist_kd:.4f} BF={dist_bf:.4f}"
    )
    print(f" test_vecino_cercano_correctitud  (dist={dist_kd:.2f} m)")

def test_radio_cero():
    """Radio 0 solo debe devolver el punto exacto si está en la lista."""
    punto_exacto = puntos[0]
    resultado = busqueda_radio(arbol, punto_exacto, 0.0)
    assert punto_exacto in resultado
    print("  test_radio_cero")

def test_radio_gigante():
    """Radio enorme debe devolver todos los puntos."""
    resultado = busqueda_radio(arbol, puntos[0], radio=1e12)
    assert len(resultado) == len(puntos)
    print(f"  test_radio_gigante  ({len(resultado):,} puntos)")

# Ejecutar pruebas
test_distancia_2d()
test_distancia_kd()
test_arbol_un_punto()
test_arbol_vacio()
test_busqueda_radio_correctitud()
test_vecino_cercano_correctitud()
test_radio_cero()
test_radio_gigante()
print()


# ──────────────────────────────────────────────
# 4. PUNTOS DE CONSULTA (5 pruebas, radio 500 m)
# ──────────────────────────────────────────────

# Elegimos 5 puntos bien distribuidos en los datos
xs = [p[0] for p in puntos]
ys = [p[1] for p in puntos]
cx = sum(xs) / len(xs)
cy = sum(ys) / len(ys)
rango_x = max(xs) - min(xs)
rango_y = max(ys) - min(ys)

# Puntos de consulta: centro y cuatro cuadrantes
puntos_consulta = [
    (cx,                   cy,                   "Centro"),
    (cx - rango_x * 0.25,  cy + rango_y * 0.25,  "Cuadrante NW"),
    (cx + rango_x * 0.25,  cy + rango_y * 0.25,  "Cuadrante NE"),
    (cx - rango_x * 0.25,  cy - rango_y * 0.25,  "Cuadrante SW"),
    (cx + rango_x * 0.25,  cy - rango_y * 0.25,  "Cuadrante SE"),
]

print("=" * 55)
print(f"  BÚSQUEDAS — Radio: {RADIO_METROS} m")
print("=" * 55)

resultados_por_punto = []
for px, py, nombre in puntos_consulta:
    punto_q = (px, py)
    res = busqueda_radio(arbol, punto_q, RADIO_METROS)
    vec, dist = vecino_cercano(arbol, punto_q)
    resultados_por_punto.append((punto_q, nombre, res, vec, dist))
    print(f"  [{nombre}]")
    print(f"    Consulta     : ({px:,.0f}, {py:,.0f}) m")
    print(f"    Vecinos 500m : {len(res)} puntos")
    if vec:
        print(f"    Más cercano  : ({vec[0]:,.0f}, {vec[1]:,.0f}) m — {dist:.2f} m")
    print()


# ──────────────────────────────────────────────
# 5. AUXILIAR: DIBUJAR LÍNEAS DEL KD-TREE
# ──────────────────────────────────────────────

def dibujar_kdtree(nodo, xmin, xmax, ymin, ymax, ax, nivel=0, max_nivel=6):
    """
    Dibuja recursivamente las líneas de partición del KD-Tree.
    Se limita a `max_nivel` niveles para no saturar la figura.
    """
    if nodo is None or nivel > max_nivel:
        return

    x, y = nodo.punto[0], nodo.punto[1]

    if nodo.eje == 0:                         # divide en X → línea vertical
        ax.plot([x, x], [ymin, ymax],
                color="royalblue", alpha=max(0.08, 0.5 - nivel * 0.07),
                linewidth=max(0.3, 1.5 - nivel * 0.2), linestyle="--")
        dibujar_kdtree(nodo.izquierda, xmin, x,    ymin, ymax, ax, nivel+1, max_nivel)
        dibujar_kdtree(nodo.derecha,   x,    xmax,  ymin, ymax, ax, nivel+1, max_nivel)
    else:                                     # divide en Y → línea horizontal
        ax.plot([xmin, xmax], [y, y],
                color="darkorange", alpha=max(0.08, 0.5 - nivel * 0.07),
                linewidth=max(0.3, 1.5 - nivel * 0.2), linestyle="--")
        dibujar_kdtree(nodo.izquierda, xmin, xmax, ymin, y,    ax, nivel+1, max_nivel)
        dibujar_kdtree(nodo.derecha,   xmin, xmax, y,    ymax,  ax, nivel+1, max_nivel)

# ──────────────────────────────────────────────
# AUXILIAR: KD-TREE ESTILO PARTICIONES (MEDIANAS)
# ──────────────────────────────────────────────

def dibujar_kdtree_particiones(nodo, xmin, xmax, ymin, ymax, ax):
    """
    Dibuja el KD-Tree mostrando explícitamente las particiones por mediana.

    A diferencia de la función estándar, aquí las líneas representan
    los planos de corte completos (como en diagramas teóricos),
    permitiendo visualizar cómo el espacio se divide recursivamente.

    Se usa únicamente en la visualización unificada final.
    """

    if nodo is None:
        return

    x, y = nodo.punto
    eje = nodo.eje

    if eje == 0:
        # División vertical (por X)
        ax.plot([x, x], [ymin, ymax],
                linestyle="--", color="#3a86ff", linewidth=1.5)

        dibujar_kdtree_particiones(nodo.izquierda, xmin, x, ymin, ymax, ax)
        dibujar_kdtree_particiones(nodo.derecha, x, xmax, ymin, ymax, ax)

    else:
        # División horizontal (por Y)
        ax.plot([xmin, xmax], [y, y],
                linestyle="--", color="#8ac926", linewidth=1.5)

        dibujar_kdtree_particiones(nodo.izquierda, xmin, xmax, ymin, y, ax)
        dibujar_kdtree_particiones(nodo.derecha, xmin, xmax, y, ymax, ax)
# ──────────────────────────────────────────────
# 6. FIGURA GLOBAL: todos los puntos + árbol + consultas
# ──────────────────────────────────────────────

print("Generando visualizaciones...")

fig_global, ax_g = plt.subplots(figsize=(11, 9))
fig_global.patch.set_facecolor("#0f0f1a")
ax_g.set_facecolor("#0f0f1a")

# Todos los puntos (fondo)
ax_g.scatter(xs, ys, s=0.8, color="#4a9eff", alpha=0.25, zorder=1)

# Líneas del KD-Tree (primeros 7 niveles)
dibujar_kdtree(arbol, min(xs), max(xs), min(ys), max(ys), ax_g, max_nivel=7)

# Para cada punto de consulta: radio + vecinos + vecino más cercano
colores_consulta = ["#ff4d4d", "#ff9f1c", "#2ec4b6", "#e040fb", "#76ff03"]
for idx, (punto_q, nombre, res, vec, dist) in enumerate(resultados_por_punto):
    col = colores_consulta[idx]

    # Puntos dentro del radio
    if res:
        xr = [p[0] for p in res]
        yr = [p[1] for p in res]
        ax_g.scatter(xr, yr, s=12, color=col, alpha=0.7, zorder=3)

    # Círculo del radio
    circulo = mpatches.Circle(
        (punto_q[0], punto_q[1]), RADIO_METROS,
        fill=True, facecolor=col, alpha=0.06,
        edgecolor=col, linewidth=1.2, zorder=4
    )
    ax_g.add_patch(circulo)

    # Punto de consulta
    ax_g.scatter(punto_q[0], punto_q[1], s=90, color=col,
                 edgecolors="white", linewidths=0.8, zorder=5,
                 label=f"{nombre} ({len(res)} vecinos)")

    # Línea al vecino más cercano
    if vec:
        ax_g.plot([punto_q[0], vec[0]], [punto_q[1], vec[1]],
                  color=col, linewidth=1.5, linestyle="-", zorder=4, alpha=0.9)
        ax_g.scatter(vec[0], vec[1], s=60, marker="*",
                     color="white", edgecolors=col, linewidths=0.8, zorder=6)

ax_g.set_title("KD-Tree — Medellín | 5 consultas, radio 500 m",
               color="white", fontsize=13, pad=12)
ax_g.set_xlabel("X (metros, EPSG:3116)", color="#aaaaaa")
ax_g.set_ylabel("Y (metros, EPSG:3116)", color="#aaaaaa")
ax_g.tick_params(colors="#aaaaaa")
for spine in ax_g.spines.values():
    spine.set_edgecolor("#333355")
leg = ax_g.legend(loc="upper right", fontsize=8,
                  facecolor="#1a1a2e", edgecolor="#333355", labelcolor="white")
plt.tight_layout()
plt.savefig("vista_global.png", dpi=150, bbox_inches="tight",
            facecolor=fig_global.get_facecolor())
plt.show()
print("  vista_global.png")


# ──────────────────────────────────────────────
# 7. ZOOM POR PUNTO: radio + árbol + conexiones
# ──────────────────────────────────────────────

def visualizar_zoom(punto_q, nombre, res, vec, dist, arbol, idx):
    """
    Zoom al radio del punto de consulta.
    Muestra:
      - Líneas del KD-Tree recortadas al área del zoom
      - Puntos dentro del radio (conectados con líneas al centro)
      - Círculo del radio
      - Vecino más cercano destacado
    """
    margen = RADIO_METROS * 1.3
    xmin_z = punto_q[0] - margen
    xmax_z = punto_q[0] + margen
    ymin_z = punto_q[1] - margen
    ymax_z = punto_q[1] + margen

    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    # Líneas del árbol en el área del zoom (niveles profundos visibles aquí)
    dibujar_kdtree(arbol, xmin_z, xmax_z, ymin_z, ymax_z, ax, max_nivel=12)

    col = colores_consulta[idx]

    # Líneas de conexión del centro a cada vecino
    for p in res:
        ax.plot([punto_q[0], p[0]], [punto_q[1], p[1]],
                color=col, alpha=0.18, linewidth=0.7, zorder=2)

    # Puntos dentro del radio
    if res:
        xr = [p[0] for p in res]
        yr = [p[1] for p in res]
        ax.scatter(xr, yr, s=25, color=col, alpha=0.85,
                   edgecolors="white", linewidths=0.3, zorder=4,
                   label=f"Vecinos: {len(res)}")

    # Punto de consulta
    ax.scatter(punto_q[0], punto_q[1], s=160, color="white",
               edgecolors=col, linewidths=2, zorder=6, label="Consulta")

    # Vecino más cercano
    if vec:
        ax.scatter(vec[0], vec[1], s=200, marker="*",
                   color="#ffd700", edgecolors="white", linewidths=0.8,
                   zorder=7, label=f"Más cercano ({dist:.1f} m)")
        ax.plot([punto_q[0], vec[0]], [punto_q[1], vec[1]],
                color="#ffd700", linewidth=2, linestyle="-", zorder=5)

    # Círculo del radio
    circulo = mpatches.Circle(
        (punto_q[0], punto_q[1]), RADIO_METROS,
        fill=True, facecolor=col, alpha=0.07,
        edgecolor=col, linewidth=2, linestyle="--", zorder=3
    )
    ax.add_patch(circulo)

    # Anotación de la distancia
    if vec:
        mx = (punto_q[0] + vec[0]) / 2
        my = (punto_q[1] + vec[1]) / 2
        ax.annotate(f"{dist:.1f} m", (mx, my),
                    color="#ffd700", fontsize=8, ha="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="#0d1117", alpha=0.7))

    ax.set_xlim(xmin_z, xmax_z)
    ax.set_ylim(ymin_z, ymax_z)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(f"Zoom — {nombre} | radio {RADIO_METROS} m",
                 color="white", fontsize=11)
    ax.set_xlabel("X (m)", color="#aaaaaa")
    ax.set_ylabel("Y (m)", color="#aaaaaa")
    ax.tick_params(colors="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333355")

    leg = ax.legend(loc="upper right", fontsize=8,
                    facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
    plt.tight_layout()
    nombre_archivo = f"zoom_{nombre.lower().replace(' ', '_')}.png"
    plt.savefig(nombre_archivo, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print(f"  {nombre_archivo}")


for idx, (punto_q, nombre, res, vec, dist) in enumerate(resultados_por_punto):
    visualizar_zoom(punto_q, nombre, res, vec, dist, arbol, idx)

# ──────────────────────────────────────────────
# 8. VISUALIZACIÓN UNIFICADA (ÁRBOL + PUNTOS + RADIO)
# ──────────────────────────────────────────────

def visualizar_union(arbol, puntos, resultados_por_punto):
    """
    Visualización unificada del sistema:

    Muestra en una sola gráfica:
        - Todos los puntos del dataset
        - Las divisiones del KD-Tree
        - El punto de consulta
        - Los puntos dentro del radio
        - El vecino más cercano
        - El círculo del radio

    Objetivo:
        Facilitar la interpretación espacial del algoritmo y cómo el árbol
        divide el espacio en relación con la búsqueda.
    """

    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]

    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    # ─── Todos los puntos ───
    ax.scatter(xs, ys, s=5, color="#6fa8dc", alpha=0.25, label="Todos los puntos")

    # ─── Divisiones del KD-Tree ───
    dibujar_kdtree_particiones(arbol, min(xs), max(xs), min(ys), max(ys), ax)

    for punto_q, nombre, res, vec, dist in resultados_por_punto:

        # Punto de consulta
        ax.scatter(punto_q[0], punto_q[1],
                   s=120, color="#00ffcc",
                   edgecolors="white", linewidths=1.2,
                   label="Consulta")

        # Círculo del radio
        circulo = mpatches.Circle(
            punto_q, RADIO_METROS,
            fill=False, edgecolor="white",
            linewidth=2, linestyle="--"
        )
        ax.add_patch(circulo)

        # Puntos dentro del radio
        if res:
            xr = [p[0] for p in res]
            yr = [p[1] for p in res]
            ax.scatter(xr, yr,
                       s=30, color="#ff6b6b",
                       alpha=0.8, label="Dentro del radio")

        # Vecino más cercano
        if vec:
            ax.scatter(vec[0], vec[1],
                       s=150, marker="*",
                       color="#ffd700",
                       edgecolors="white",
                       label="Más cercano")

            ax.plot([punto_q[0], vec[0]],
                    [punto_q[1], vec[1]],
                    color="#ffd700", linewidth=2)

    # ─── Estética ───
    ax.set_title("Visualización unificada — KD-Tree + búsqueda espacial",
                 color="white", fontsize=13)

    ax.set_xlabel("X (metros)", color="#aaaaaa")
    ax.set_ylabel("Y (metros)", color="#aaaaaa")

    ax.tick_params(colors="#aaaaaa")

    for spine in ax.spines.values():
        spine.set_edgecolor("#333355")

    # Eliminar duplicados en la leyenda
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(),
              facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")

    plt.tight_layout()
    plt.savefig("union_kdtree.png", dpi=150)
    plt.show()

    print("  union_kdtree.png")
visualizar_union(arbol, puntos, resultados_por_punto)

print("\nTodas las pruebas y visualizaciones completadas.")
