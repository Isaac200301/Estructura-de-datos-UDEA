# Quadtree simple en 2D
# Guarda puntos (x, y) y permite buscar por radio
# y encontrar el vecino más cercano

import math

CAPACIDAD = 4


# -----------------------------
# Clase nodo
# -----------------------------

class Nodo:
    def __init__(self, xmin, xmax, ymin, ymax, capacidad=CAPACIDAD, nivel=0):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        self.capacidad = capacidad
        self.nivel = nivel

        self.puntos = []

        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None

        self.dividido = False

    def es_hoja(self):
        return not self.dividido

    def __repr__(self):
        return f"Nodo(x=[{self.xmin},{self.xmax}], y=[{self.ymin},{self.ymax}], puntos={len(self.puntos)})"


# -----------------------------
# Distancia
# -----------------------------

def distancia(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx*dx + dy*dy)


# -----------------------------
# Subdividir nodo
# -----------------------------

def subdividir(nodo):
    cx = (nodo.xmin + nodo.xmax) / 2
    cy = (nodo.ymin + nodo.ymax) / 2

    nodo.nw = Nodo(nodo.xmin, cx, cy, nodo.ymax, nodo.capacidad, nodo.nivel+1)
    nodo.ne = Nodo(cx, nodo.xmax, cy, nodo.ymax, nodo.capacidad, nodo.nivel+1)
    nodo.sw = Nodo(nodo.xmin, cx, nodo.ymin, cy, nodo.capacidad, nodo.nivel+1)
    nodo.se = Nodo(cx, nodo.xmax, nodo.ymin, cy, nodo.capacidad, nodo.nivel+1)

    nodo.dividido = True

    puntos_viejos = nodo.puntos
    nodo.puntos = []

    for p in puntos_viejos:
        insertar(nodo, p)


# -----------------------------
# Insertar punto
# -----------------------------

def insertar(nodo, punto):
    x, y = punto

    # si el punto no está en la zona
    if not (nodo.xmin <= x <= nodo.xmax and nodo.ymin <= y <= nodo.ymax):
        return False

    # si es hoja
    if nodo.es_hoja():
        if len(nodo.puntos) < nodo.capacidad:
            nodo.puntos.append(punto)
            return True
        else:
            subdividir(nodo)
            return insertar(nodo, punto)

    # si ya está dividido
    if insertar(nodo.nw, punto): return True
    if insertar(nodo.ne, punto): return True
    if insertar(nodo.sw, punto): return True
    if insertar(nodo.se, punto): return True

    return False


# -----------------------------
# Construir árbol
# -----------------------------

def construir_quadtree(puntos):
    if not puntos:
        return None

    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]

    raiz = Nodo(
        min(xs)-1, max(xs)+1,
        min(ys)-1, max(ys)+1
    )

    for p in puntos:
        insertar(raiz, p)

    return raiz


# -----------------------------
# Ver si círculo toca la caja
# -----------------------------

def intersecta(cx, cy, r, xmin, xmax, ymin, ymax):
    px = max(xmin, min(cx, xmax))
    py = max(ymin, min(cy, ymax))

    dx = cx - px
    dy = cy - py

    return dx*dx + dy*dy <= r*r


# -----------------------------
# Búsqueda por radio
# -----------------------------

def buscar_radio(nodo, punto, radio, resultado=None):
    if resultado is None:
        resultado = []

    if nodo is None:
        return resultado

    # poda
    if not intersecta(punto[0], punto[1], radio,
                      nodo.xmin, nodo.xmax,
                      nodo.ymin, nodo.ymax):
        return resultado

    # revisar puntos
    for p in nodo.puntos:
        if distancia(p, punto) <= radio:
            resultado.append(p)

    # ir a hijos
    if nodo.dividido:
        buscar_radio(nodo.nw, punto, radio, resultado)
        buscar_radio(nodo.ne, punto, radio, resultado)
        buscar_radio(nodo.sw, punto, radio, resultado)
        buscar_radio(nodo.se, punto, radio, resultado)

    return resultado


# -----------------------------
# Distancia mínima a caja
# -----------------------------

def dist_caja(punto, xmin, xmax, ymin, ymax):
    dx = max(xmin - punto[0], 0, punto[0] - xmax)
    dy = max(ymin - punto[1], 0, punto[1] - ymax)
    return math.sqrt(dx*dx + dy*dy)


# -----------------------------
# Vecino más cercano
# -----------------------------

def vecino_mas_cercano(nodo, punto, mejor=None):
    if nodo is None:
        return mejor

    # revisar puntos del nodo
    for p in nodo.puntos:
        d = distancia(p, punto)
        if mejor is None or d < mejor[1]:
            mejor = (p, d)

    # revisar hijos
    if nodo.dividido:
        mejor = vecino_mas_cercano(nodo.nw, punto, mejor)
        mejor = vecino_mas_cercano(nodo.ne, punto, mejor)
        mejor = vecino_mas_cercano(nodo.sw, punto, mejor)
        mejor = vecino_mas_cercano(nodo.se, punto, mejor)

    return mejor
# -----------------------------
# Fuerza bruta (para comparar)
# -----------------------------

def buscar_bruta(puntos, punto, radio):
    res = []
    for p in puntos:
        if distancia(p, punto) <= radio:
            res.append(p)
    return res


def vecino_bruta(puntos, punto):
    mejor_p = None
    mejor_d = float("inf")

    for p in puntos:
        d = distancia(p, punto)
        if d < mejor_d:
            mejor_d = d
            mejor_p = p

    return mejor_p, mejor_d

# -----------------------------
# Alias para compatibilidad con otros archivos
# -----------------------------

busqueda_radio = buscar_radio
vecino_cercano = vecino_mas_cercano
busqueda_fuerza_bruta = buscar_bruta
