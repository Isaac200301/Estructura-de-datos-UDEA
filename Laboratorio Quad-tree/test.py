# test.py
# Pruebas y visualización del Quadtree

import random
import pyproj
import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from Quadtree import (
    construir_quadtree,
    buscar_radio,
    vecino_mas_cercano,
    buscar_bruta,
    vecino_bruta,
    distancia
)

# -----------------------------
# CONFIG
# -----------------------------

CIUDAD = "Medellin, Colombia"
RADIO = 500
random.seed(42)

# Colores sobrios
COLOR_PUNTOS = "#6c757d"
COLOR_ARBOL  = "#adb5bd"
COLOR_QUERY  = "#1971c2"
COLOR_VECINO = "#0b7285"

# -----------------------------
# 1. CARGAR DATOS
# -----------------------------

print("Cargando datos...")

datos = ox.features_from_place(CIUDAD, tags={"building": True})
datos["centroide"] = datos.geometry.centroid

latlon = [(p.y, p.x) for p in datos["centroide"] if p is not None]
latlon = random.sample(latlon, min(8000, len(latlon)))

transformador = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3116", always_xy=True)

puntos = [transformador.transform(lon, lat) for lat, lon in latlon]

print("Puntos:", len(puntos))

# -----------------------------
# 2. CONSTRUIR ÁRBOL
# -----------------------------

print("Construyendo Quadtree...")
arbol = construir_quadtree(puntos)
print("Listo\n")

# -----------------------------
# 3. PRUEBAS RÁPIDAS
# -----------------------------

print("Probando...")

assert distancia((0, 0), (3, 4)) == 5.0

muestra = random.sample(puntos, 200)
p = random.choice(muestra)

qt = construir_quadtree(muestra)

res1 = set(buscar_radio(qt, p, RADIO))
res2 = set(buscar_bruta(muestra, p, RADIO))

assert res1 == res2

vec1 = vecino_mas_cercano(qt, p)
vec2 = vecino_bruta(muestra, p)

if vec1:
    _, d1 = vec1
    _, d2 = vec2
    assert abs(d1 - d2) < 1e-6

print("Todo bien 👍\n")

# -----------------------------
# 4. PUNTOS DE CONSULTA (separados)
# -----------------------------

xs = [p[0] for p in puntos]
ys = [p[1] for p in puntos]

cx = sum(xs) / len(xs)
cy = sum(ys) / len(ys)

rx = max(xs) - min(xs)
ry = max(ys) - min(ys)

consultas = [
    (cx, cy, "Centro"),
    (cx - rx*0.4, cy + ry*0.4, "NW"),
    (cx + rx*0.4, cy + ry*0.4, "NE"),
    (cx - rx*0.4, cy - ry*0.4, "SW"),
    (cx + rx*0.4, cy - ry*0.4, "SE"),
]

resultados = []

for x, y, nombre in consultas:
    q = (x, y)
    vecinos = buscar_radio(arbol, q, RADIO)
    vec = vecino_mas_cercano(arbol, q)

    resultados.append((q, nombre, vecinos, vec))

    print(nombre, "→ vecinos:", len(vecinos))

# -----------------------------
# 5. DIBUJAR QUADTREE
# -----------------------------

def dibujar(nodo, ax):
    if nodo is None:
        return

    rect = patches.Rectangle(
        (nodo.xmin, nodo.ymin),
        nodo.xmax - nodo.xmin,
        nodo.ymax - nodo.ymin,
        fill=False,
        edgecolor=COLOR_ARBOL,
        linewidth=0.4
    )
    ax.add_patch(rect)

    if nodo.dividido:
        dibujar(nodo.nw, ax)
        dibujar(nodo.ne, ax)
        dibujar(nodo.sw, ax)
        dibujar(nodo.se, ax)

# -----------------------------
# 6. VISTA GLOBAL
# -----------------------------

print("\nMostrando vista global...")

fig, ax = plt.subplots(figsize=(10, 8))

# puntos
ax.scatter(xs, ys, s=1, color=COLOR_PUNTOS, alpha=0.3)

# árbol
dibujar(arbol, ax)

# consultas
for q, nombre, vecinos, vec in resultados:

    # círculo
    circ = patches.Circle(q, RADIO, fill=True,
                          alpha=0.08, color=COLOR_QUERY)
    ax.add_patch(circ)

    # punto
    ax.scatter(q[0], q[1], color=COLOR_QUERY, s=60)

    # vecinos
    if vecinos:
        ax.scatter([p[0] for p in vecinos],
                   [p[1] for p in vecinos],
                   color=COLOR_QUERY, s=8)

    # vecino más cercano
    if vec:
        punto, dist = vec
        ax.plot([q[0], punto[0]], [q[1], punto[1]],
                color=COLOR_VECINO)
        ax.scatter(punto[0], punto[1],
                   color=COLOR_VECINO, s=40)

ax.set_title("Quadtree Medellin (vista global)")
plt.show()

# -----------------------------
# 7. ZOOM
# -----------------------------

def zoom(q, nombre, vecinos, vec):

    margen = RADIO * 1.5

    fig, ax = plt.subplots(figsize=(6, 6))

    dibujar(arbol, ax)

    # vecinos
    if vecinos:
        ax.scatter([p[0] for p in vecinos],
                   [p[1] for p in vecinos],
                   color=COLOR_QUERY, s=15)

    # punto
    ax.scatter(q[0], q[1], color="black", s=80)

    # círculo
    circ = patches.Circle(q, RADIO, fill=False,
                          edgecolor=COLOR_QUERY)
    ax.add_patch(circ)

    # vecino cercano
    if vec:
        p, d = vec
        ax.scatter(p[0], p[1], color=COLOR_VECINO, s=80)
        ax.plot([q[0], p[0]], [q[1], p[1]], color=COLOR_VECINO)

    ax.set_xlim(q[0] - margen, q[0] + margen)
    ax.set_ylim(q[1] - margen, q[1] + margen)

    ax.set_title(f"Zoom {nombre}")
    plt.show()


for q, nombre, vecinos, vec in resultados:
    zoom(q, nombre, vecinos, vec)

print("\nTodo listo 🚀")
