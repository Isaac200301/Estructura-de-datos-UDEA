"""
test.py
=======
Pruebas unitarias, visualizaciones y análisis del Quadtree.

Incluye:
    - Verificación de correctitud (Quadtree vs fuerza bruta)
    - Múltiples puntos de consulta con radio fijo de 500 m
    - Visualización global con rectángulos del Quadtree
    - Zoom al radio de cada punto mostrando la subdivisión y vecinos
    - Conexiones entre el punto y sus vecinos encontrados
"""

import random
import math
import pyproj
import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from Quadtree import (
    NodoCuad,
    construir_quadtree,
    busqueda_radio,
    vecino_cercano,
    busqueda_fuerza_bruta,
    vecino_bruta,
    calcular_distancia,
)

# ─────────────────────────────────────────────────────────
# 1. CARGA Y PROYECCIÓN DE DATOS
# ─────────────────────────────────────────────────────────

CIUDAD       = "Medellin, Colombia"
RADIO_METROS = 500
SEMILLA      = 42
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

# Proyectar a metros (EPSG:3116 — sistema metrico Colombia)
# Sin esta proyeccion las distancias estarian en grados, no en metros.
transformador = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3116", always_xy=True)

puntos = [
    tuple(transformador.transform(lon, lat))
    for lat, lon in lista_latlon
]
print(f"  Proyeccion: EPSG:3116 (metros)\n")


# ─────────────────────────────────────────────────────────
# 2. CONSTRUCCIÓN DEL ÁRBOL
# ─────────────────────────────────────────────────────────

print("Construyendo Quadtree...")
arbol = construir_quadtree(puntos, capacidad=4)
print("  Arbol construido correctamente\n")


# ─────────────────────────────────────────────────────────
# 3. PRUEBAS UNITARIAS
# ─────────────────────────────────────────────────────────

print("=" * 55)
print("  PRUEBAS UNITARIAS")
print("=" * 55)


def test_distancia_basica():
    # Triangulo 3-4-5
    assert abs(calcular_distancia((0, 0), (3, 4)) - 5.0) < 1e-9
    assert calcular_distancia((1, 1), (1, 1)) == 0.0
    print("  OK  test_distancia_basica")


def test_arbol_vacio():
    assert construir_quadtree([]) is None
    print("  OK  test_arbol_vacio")


def test_arbol_un_punto():
    qt  = construir_quadtree([(1.0, 2.0)])
    res = busqueda_radio(qt, (1.0, 2.0), 1.0)
    assert (1.0, 2.0) in res
    print("  OK  test_arbol_un_punto")


def test_todos_los_puntos_insertados():
    """El Quadtree debe encontrar todos los puntos con radio enorme."""
    muestra = random.sample(puntos, 200)
    qt = construir_quadtree(muestra)
    centro = (
        sum(p[0] for p in muestra) / len(muestra),
        sum(p[1] for p in muestra) / len(muestra),
    )
    res = busqueda_radio(qt, centro, radio=1e12)
    assert len(res) == len(muestra), (
        f"Esperados {len(muestra)}, encontrados {len(res)}"
    )
    print(f"  OK  test_todos_los_puntos_insertados  ({len(res)} puntos)")


def test_busqueda_radio_correctitud():
    """El Quadtree debe devolver exactamente los mismos puntos que fuerza bruta."""
    muestra = random.sample(puntos, 300)
    punto_q = random.choice(muestra)

    qt     = construir_quadtree(muestra)
    res_qt = set(busqueda_radio(qt, punto_q, RADIO_METROS))
    res_bf = set(busqueda_fuerza_bruta(muestra, punto_q, RADIO_METROS))

    assert res_qt == res_bf, (
        f"Diferencia: QT={len(res_qt)}, BF={len(res_bf)}"
    )
    print(f"  OK  test_busqueda_radio_correctitud  ({len(res_qt)} pts en radio)")


def test_vecino_cercano_correctitud():
    """El vecino del Quadtree debe coincidir con fuerza bruta."""
    muestra = random.sample(puntos, 500)
    punto_q = (
        random.uniform(min(p[0] for p in muestra), max(p[0] for p in muestra)),
        random.uniform(min(p[1] for p in muestra), max(p[1] for p in muestra)),
    )
    qt = construir_quadtree(muestra)

    vec_qt, dist_qt = vecino_cercano(qt, punto_q)
    _,      dist_bf = vecino_bruta(muestra, punto_q)

    assert abs(dist_qt - dist_bf) < 1e-6, (
        f"Distancias distintas: QT={dist_qt:.4f}, BF={dist_bf:.4f}"
    )
    print(f"  OK  test_vecino_cercano_correctitud  (dist={dist_qt:.2f} m)")


def test_radio_cero():
    """Radio 0 solo debe devolver el punto exacto si esta en la lista."""
    punto_exacto = puntos[0]
    qt  = construir_quadtree(puntos[:100])
    res = busqueda_radio(qt, punto_exacto, 0.0)
    assert punto_exacto in res
    print("  OK  test_radio_cero")


def test_radio_gigante():
    """Radio enorme debe devolver todos los puntos."""
    muestra = random.sample(puntos, 200)
    qt  = construir_quadtree(muestra)
    res = busqueda_radio(qt, muestra[0], radio=1e12)
    assert len(res) == len(muestra)
    print(f"  OK  test_radio_gigante  ({len(res)} puntos)")


# Ejecutar todas las pruebas
test_distancia_basica()
test_arbol_vacio()
test_arbol_un_punto()
test_todos_los_puntos_insertados()
test_busqueda_radio_correctitud()
test_vecino_cercano_correctitud()
test_radio_cero()
test_radio_gigante()
print()


# ─────────────────────────────────────────────────────────
# 4. PUNTOS DE CONSULTA (5 zonas, radio 500 m)
# ─────────────────────────────────────────────────────────

xs = [p[0] for p in puntos]
ys = [p[1] for p in puntos]
cx = sum(xs) / len(xs)
cy = sum(ys) / len(ys)
rx = max(xs) - min(xs)
ry = max(ys) - min(ys)

PUNTOS_CONSULTA = [
    (cx,            cy,            "Centro"),
    (cx - rx*0.25,  cy + ry*0.25,  "Cuadrante NW"),
    (cx + rx*0.25,  cy + ry*0.25,  "Cuadrante NE"),
    (cx - rx*0.25,  cy - ry*0.25,  "Cuadrante SW"),
    (cx + rx*0.25,  cy - ry*0.25,  "Cuadrante SE"),
]
COLORES = ["#ff4d4d", "#ff9f1c", "#2ec4b6", "#e040fb", "#76ff03"]

print("=" * 55)
print(f"  BUSQUEDAS — Radio: {RADIO_METROS} m")
print("=" * 55)

resultados_por_punto = []
for px, py, nombre in PUNTOS_CONSULTA:
    q   = (px, py)
    res = busqueda_radio(arbol, q, RADIO_METROS)
    vec, dist = vecino_cercano(arbol, q)
    resultados_por_punto.append((q, nombre, res, vec, dist))
    print(f"  [{nombre}]")
    print(f"    Consulta     : ({px:,.0f}, {py:,.0f}) m")
    print(f"    Vecinos 500m : {len(res)} puntos")
    if vec:
        print(f"    Mas cercano  : ({vec[0]:,.0f}, {vec[1]:,.0f}) m — {dist:.2f} m")
    print()


# ─────────────────────────────────────────────────────────
# 5. FUNCIÓN PARA DIBUJAR EL QUADTREE (rectangulos anidados)
# ─────────────────────────────────────────────────────────

def dibujar_quadtree(nodo, ax, nivel=0, max_nivel=7):
    """
    Dibuja recursivamente los rectangulos del Quadtree.

    La visualizacion caracteristica del Quadtree son rectangulos
    anidados que se hacen mas pequeños donde hay mas puntos.
    Esto es muy distinto al KD-Tree que muestra lineas infinitas.
    """
    if nodo is None or nivel > max_nivel:
        return

    alpha = max(0.06, 0.65 - nivel * 0.09)
    lw    = max(0.2,  1.8  - nivel * 0.22)

    rect = mpatches.Rectangle(
        (nodo.xmin, nodo.ymin),
        nodo.xmax - nodo.xmin,
        nodo.ymax - nodo.ymin,
        fill=False,
        edgecolor="#4a9eff",
        alpha=alpha,
        linewidth=lw,
    )
    ax.add_patch(rect)

    if nodo.dividido:
        dibujar_quadtree(nodo.nw, ax, nivel + 1, max_nivel)
        dibujar_quadtree(nodo.ne, ax, nivel + 1, max_nivel)
        dibujar_quadtree(nodo.sw, ax, nivel + 1, max_nivel)
        dibujar_quadtree(nodo.se, ax, nivel + 1, max_nivel)


# ─────────────────────────────────────────────────────────
# 6. FIGURA GLOBAL
# ─────────────────────────────────────────────────────────

print("Generando visualizaciones...")

fig_g, ax_g = plt.subplots(figsize=(11, 9))
fig_g.patch.set_facecolor("#0f0f1a")
ax_g.set_facecolor("#0f0f1a")

ax_g.scatter(xs, ys, s=0.7, color="#4a9eff", alpha=0.22, zorder=1)
dibujar_quadtree(arbol, ax_g, max_nivel=7)

for idx, (q, nombre, res, vec, dist) in enumerate(resultados_por_punto):
    col = COLORES[idx]
    if res:
        ax_g.scatter([p[0] for p in res], [p[1] for p in res],
                     s=11, color=col, alpha=0.75, zorder=3)
    circ = mpatches.Circle(q, RADIO_METROS, fill=True,
                            facecolor=col, alpha=0.07,
                            edgecolor=col, linewidth=1.3, zorder=4)
    ax_g.add_patch(circ)
    ax_g.scatter(q[0], q[1], s=95, color=col,
                 edgecolors="white", linewidths=0.9, zorder=5,
                 label=f"{nombre} ({len(res)} vecinos)")
    if vec:
        ax_g.plot([q[0], vec[0]], [q[1], vec[1]],
                  color=col, lw=1.5, alpha=0.9, zorder=4)
        ax_g.scatter(vec[0], vec[1], s=65, marker="*",
                     color="white", edgecolors=col, lw=0.8, zorder=6)

ax_g.set_title("Quadtree — Medellin | 5 consultas, radio 500 m",
               color="white", fontsize=13, pad=12)
ax_g.set_xlabel("X (metros, EPSG:3116)", color="#aaaaaa")
ax_g.set_ylabel("Y (metros, EPSG:3116)", color="#aaaaaa")
ax_g.tick_params(colors="#aaaaaa")
for sp in ax_g.spines.values():
    sp.set_edgecolor("#333355")
ax_g.legend(loc="upper right", fontsize=8,
            facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
plt.tight_layout()
plt.savefig("vista_global.png", dpi=150, bbox_inches="tight",
            facecolor=fig_g.get_facecolor())
plt.show()
print("  OK  vista_global.png")


# ─────────────────────────────────────────────────────────
# 7. ZOOM POR PUNTO DE CONSULTA
# ─────────────────────────────────────────────────────────

def visualizar_zoom(q, nombre, res, vec, dist, arbol, idx):
    """
    Zoom al area del radio.
    Los rectangulos del Quadtree dentro de la zona son muy claros:
    se ven las subdivisiones exactas que el arbol hizo en esa region.
    """
    col    = COLORES[idx]
    margen = RADIO_METROS * 1.3
    xz = (q[0] - margen, q[0] + margen)
    yz = (q[1] - margen, q[1] + margen)

    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    # Rectangulos del Quadtree (mas niveles visibles en el zoom)
    dibujar_quadtree(arbol, ax, max_nivel=15)

    # Lineas de cada vecino al punto central
    for p in res:
        ax.plot([q[0], p[0]], [q[1], p[1]],
                color=col, alpha=0.18, lw=0.7, zorder=2)

    if res:
        ax.scatter([p[0] for p in res], [p[1] for p in res],
                   s=28, color=col, alpha=0.88,
                   edgecolors="white", lw=0.3, zorder=4,
                   label=f"Vecinos: {len(res)}")

    ax.scatter(q[0], q[1], s=180, color="white",
               edgecolors=col, lw=2.5, zorder=6, label="Punto consulta")

    if vec:
        ax.scatter(vec[0], vec[1], s=220, marker="*",
                   color="#ffd700", edgecolors="white", lw=0.8,
                   zorder=7, label=f"Mas cercano ({dist:.1f} m)")
        ax.plot([q[0], vec[0]], [q[1], vec[1]],
                color="#ffd700", lw=2.2, zorder=5)
        mx, my = (q[0] + vec[0]) / 2, (q[1] + vec[1]) / 2
        ax.annotate(f"{dist:.1f} m", (mx, my),
                    color="#ffd700", fontsize=8.5, ha="center",
                    bbox=dict(boxstyle="round,pad=0.25",
                              fc="#0d1117", alpha=0.75))

    circ = mpatches.Circle(q, RADIO_METROS, fill=True,
                            facecolor=col, alpha=0.08,
                            edgecolor=col, lw=2, ls="--", zorder=3)
    ax.add_patch(circ)

    ax.set_xlim(*xz)
    ax.set_ylim(*yz)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(f"Zoom — {nombre} | radio {RADIO_METROS} m",
                 color="white", fontsize=11)
    ax.set_xlabel("X (m)", color="#aaaaaa")
    ax.set_ylabel("Y (m)", color="#aaaaaa")
    ax.tick_params(colors="#aaaaaa")
    for sp in ax.spines.values():
        sp.set_edgecolor("#333355")
    ax.legend(loc="upper right", fontsize=8,
              facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
    plt.tight_layout()
    fname = f"zoom_{nombre.lower().replace(' ', '_')}.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print(f"  OK  {fname}")


for idx, (q, nombre, res, vec, dist) in enumerate(resultados_por_punto):
    visualizar_zoom(q, nombre, res, vec, dist, arbol, idx)

print("\nTodas las pruebas y visualizaciones completadas.")
