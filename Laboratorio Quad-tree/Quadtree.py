"""
Quadtree.py
===========
Implementación desde cero de un Quadtree para 2D.

Nota sobre K dimensiones:
    El Quadtree divide cada región en 2^K subregiones:
      - 2D → 4 hijos  (Quadtree)
      - 3D → 8 hijos  (Octree)
      - KD → 2^K hijos → impractico para K > 3
    Por eso esta implementación es para 2D. La generalización
    natural a 3D sería un Octree, pero para este ejercicio de
    logística 2D el Quadtree es la estructura correcta.

Estructura del módulo:
    - NodoCuad           : nodo con bounding box y 4 hijos
    - construir_quadtree : inserción O(n log n)
    - busqueda_radio     : range search con poda geométrica
    - vecino_cercano     : nearest-neighbor con poda por distancia mínima
    - calcular_distancia : distancia euclidiana 2D
    - busqueda_fuerza_bruta / vecino_bruta : referencia O(n)
"""

import math
import sys

# Para árboles profundos con muchos puntos
sys.setrecursionlimit(50_000)

# Puntos máximos por nodo hoja antes de subdividir
CAPACIDAD_DEFAULT = 4


# ─────────────────────────────────────────────────────────
# Nodo del árbol
# ─────────────────────────────────────────────────────────

class NodoCuad:
    """
    Nodo de un Quadtree 2D.

    Cada nodo representa un rectángulo del plano.
    Cuando un nodo hoja se llena, se subdivide en cuatro
    cuadrantes iguales y redistribuye sus puntos.

    Los puntos se guardan SOLO en los nodos hoja (no en internos).

    Atributos:
        xmin, xmax  : límites horizontales del cuadrante
        ymin, ymax  : límites verticales del cuadrante
        capacidad   : máx. puntos antes de subdividir
        puntos      : lista de puntos almacenados (solo hojas)
        nw, ne      : hijos noroeste y noreste
        sw, se      : hijos suroeste y sureste
        dividido    : True si ya fue subdividido
        profundidad : nivel en el árbol (la raíz es 0)
        max_prof    : límite de profundidad (evita recursión infinita
                      si hay muchos puntos muy juntos)
    """

    def __init__(self, xmin, xmax, ymin, ymax,
                 capacidad=CAPACIDAD_DEFAULT, profundidad=0, max_prof=25):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.capacidad = capacidad
        self.profundidad = profundidad
        self.max_prof = max_prof

        self.puntos = []

        # Cuatro hijos: noroeste, noreste, suroeste, sureste
        self.nw = None   # x < cx,  y >= cy
        self.ne = None   # x >= cx, y >= cy
        self.sw = None   # x < cx,  y < cy
        self.se = None   # x >= cx, y < cy

        self.dividido = False

    def es_hoja(self):
        return not self.dividido

    def __repr__(self):
        return (f"NodoCuad("
                f"x=[{self.xmin:.0f},{self.xmax:.0f}], "
                f"y=[{self.ymin:.0f},{self.ymax:.0f}], "
                f"pts={len(self.puntos)}, dividido={self.dividido})")


# ─────────────────────────────────────────────────────────
# Distancia euclidiana
# ─────────────────────────────────────────────────────────

def calcular_distancia(punto_a, punto_b):
    """
    Distancia euclidiana entre dos puntos 2D.

        d = sqrt( (ax - bx)^2 + (ay - by)^2 )

    Parámetros:
        punto_a, punto_b : tuplas (x, y)

    Retorna:
        distancia (float) en las mismas unidades que los puntos
    """
    dx = punto_a[0] - punto_b[0]
    dy = punto_a[1] - punto_b[1]
    return math.sqrt(dx * dx + dy * dy)


# ─────────────────────────────────────────────────────────
# Helpers geométricos para poda
# ─────────────────────────────────────────────────────────

def _circulo_intersecta_caja(cx, cy, radio, xmin, xmax, ymin, ymax):
    """
    Verifica si un círculo y un rectángulo se intersectan.

    Idea: encontrar el punto del rectángulo más cercano al centro
    del círculo y comprobar si está dentro del radio.
    Si no hay intersección, todo ese subárbol puede descartarse.

    Retorna True si hay intersección (pueden existir puntos dentro del radio).
    """
    # Punto del rectángulo más cercano al centro del círculo
    px = max(xmin, min(cx, xmax))
    py = max(ymin, min(cy, ymax))
    dx = cx - px
    dy = cy - py
    return (dx * dx + dy * dy) <= (radio * radio)


def _dist_minima_caja(punto, xmin, xmax, ymin, ymax):
    """
    Distancia mínima de un punto al rectángulo.
    Si el punto está DENTRO del rectángulo, retorna 0.

    Usada para poda en vecino_cercano:
    si esta distancia es mayor que la mejor actual,
    ningún punto del subárbol puede ser mejor candidato.
    """
    dx = max(xmin - punto[0], 0.0, punto[0] - xmax)
    dy = max(ymin - punto[1], 0.0, punto[1] - ymax)
    return math.sqrt(dx * dx + dy * dy)


# ─────────────────────────────────────────────────────────
# Construcción del árbol (inserción punto a punto)
# ─────────────────────────────────────────────────────────

def _subdividir(nodo):
    """
    Subdivide un nodo hoja en cuatro cuadrantes iguales.

    El punto de corte es el centro del rectángulo actual.
    Luego redistribuye los puntos existentes en los nuevos hijos.

    Distribución de cuadrantes:
        NW: xmin.....cx  |  cy.....ymax
        NE: cx.....xmax  |  cy.....ymax
        SW: xmin.....cx  |  ymin.....cy
        SE: cx.....xmax  |  ymin.....cy
    """
    cx = (nodo.xmin + nodo.xmax) / 2.0
    cy = (nodo.ymin + nodo.ymax) / 2.0
    cap  = nodo.capacidad
    prof = nodo.profundidad + 1
    mp   = nodo.max_prof

    nodo.nw = NodoCuad(nodo.xmin, cx,        cy,        nodo.ymax, cap, prof, mp)
    nodo.ne = NodoCuad(cx,        nodo.xmax,  cy,        nodo.ymax, cap, prof, mp)
    nodo.sw = NodoCuad(nodo.xmin, cx,        nodo.ymin,  cy,        cap, prof, mp)
    nodo.se = NodoCuad(cx,        nodo.xmax,  nodo.ymin,  cy,        cap, prof, mp)
    nodo.dividido = True

    # Redistribuir puntos existentes en los nuevos hijos
    puntos_viejos = nodo.puntos
    nodo.puntos = []
    for p in puntos_viejos:
        _insertar(nodo, p)


def _insertar(nodo, punto):
    """
    Inserta un punto en la posición correcta del Quadtree.

    Si el nodo es hoja y tiene espacio         → guardar aquí
    Si el nodo es hoja y está lleno             → subdividir y reintentar
    Si el nodo ya está dividido                 → delegar al hijo correcto
    Si se alcanza la profundidad máxima         → guardar aquí igual
      (evita recursión infinita con puntos muy juntos)

    Parámetros:
        nodo  : NodoCuad actual
        punto : tupla (x, y)

    Retorna:
        True si se insertó, False si el punto está fuera de los límites
    """
    # El punto debe estar dentro del bounding box
    if not (nodo.xmin <= punto[0] <= nodo.xmax and
            nodo.ymin <= punto[1] <= nodo.ymax):
        return False

    if nodo.es_hoja():
        # Espacio disponible o llegamos al límite de profundidad
        if len(nodo.puntos) < nodo.capacidad or nodo.profundidad >= nodo.max_prof:
            nodo.puntos.append(punto)
            return True
        else:
            # Nodo lleno: subdividir y reintentar inserción
            _subdividir(nodo)
            return _insertar(nodo, punto)
    else:
        # Nodo interno: probar los 4 hijos en orden
        for hijo in (nodo.nw, nodo.ne, nodo.sw, nodo.se):
            if _insertar(hijo, punto):
                return True
    return False


def construir_quadtree(lista_puntos, capacidad=CAPACIDAD_DEFAULT):
    """
    Construye un Quadtree insertando los puntos de a uno.

    El bounding box inicial se calcula automáticamente.
    Se agrega un margen pequeño para evitar problemas en los bordes.

    Diferencia clave con el KD-Tree:
      - KD-Tree: construcción top-down por mediana (divide y vencerás)
      - Quadtree: construcción bottom-up por inserción y subdivisión

    Complejidad:
        Tiempo promedio : O(n log n)
        Espacio         : O(n)

    Parámetros:
        lista_puntos : lista de tuplas (x, y)
        capacidad    : puntos máximos por nodo hoja (default 4)

    Retorna:
        NodoCuad raíz, o None si la lista está vacía
    """
    if not lista_puntos:
        return None

    xs = [p[0] for p in lista_puntos]
    ys = [p[1] for p in lista_puntos]
    margen = 1.0

    raiz = NodoCuad(
        xmin=min(xs) - margen,
        xmax=max(xs) + margen,
        ymin=min(ys) - margen,
        ymax=max(ys) + margen,
        capacidad=capacidad,
    )

    for punto in lista_puntos:
        _insertar(raiz, punto)

    return raiz


# ─────────────────────────────────────────────────────────
# Búsqueda por radio (Range Search)
# ─────────────────────────────────────────────────────────

def busqueda_radio(nodo, punto_objetivo, radio, resultados=None):
    """
    Encuentra todos los puntos dentro de `radio` unidades del
    `punto_objetivo` usando el Quadtree.

    Poda geométrica (clave del algoritmo):
        Si el círculo de búsqueda NO intersecta el rectángulo del nodo,
        se descarta TODO ese subárbol sin revisar ningún punto.
        Esto es lo que hace eficiente al Quadtree.

    Complejidad promedio: O(log n + k)
        donde k = puntos encontrados

    Parámetros:
        nodo           : NodoCuad actual
        punto_objetivo : tupla (x, y) del punto de consulta
        radio          : distancia máxima (en metros)
        resultados     : lista acumuladora

    Retorna:
        lista de puntos dentro del radio
    """
    if resultados is None:
        resultados = []

    if nodo is None:
        return resultados

    # PODA: si el circulo no toca esta caja, saltamos todo el subárbol
    if not _circulo_intersecta_caja(
        punto_objetivo[0], punto_objetivo[1], radio,
        nodo.xmin, nodo.xmax, nodo.ymin, nodo.ymax
    ):
        return resultados

    # Revisar los puntos en este nodo (si es hoja)
    for punto in nodo.puntos:
        if calcular_distancia(punto, punto_objetivo) <= radio:
            resultados.append(punto)

    # Recurrir en los cuatro hijos si está dividido
    if nodo.dividido:
        busqueda_radio(nodo.nw, punto_objetivo, radio, resultados)
        busqueda_radio(nodo.ne, punto_objetivo, radio, resultados)
        busqueda_radio(nodo.sw, punto_objetivo, radio, resultados)
        busqueda_radio(nodo.se, punto_objetivo, radio, resultados)

    return resultados


# ─────────────────────────────────────────────────────────
# Vecino más cercano (Nearest Neighbor)
# ─────────────────────────────────────────────────────────

def vecino_cercano(nodo, punto_objetivo, mejor=None):
    """
    Encuentra el punto más cercano al `punto_objetivo`.

    Estrategia:
        1. Calcular la distancia mínima posible al rectángulo del nodo.
        2. Si esa distancia ya es mayor que el mejor actual → podar.
        3. Si no, revisar los puntos del nodo y actualizar el mejor.
        4. Visitar primero el cuadrante donde cae el punto objetivo
           (es el más prometedor → mejora la poda de los demás).

    Parámetros:
        nodo           : NodoCuad actual
        punto_objetivo : tupla (x, y)
        mejor          : tupla (punto, distancia) del mejor hasta ahora

    Retorna:
        (punto_mas_cercano, distancia_minima)
    """
    if nodo is None:
        return mejor

    # PODA: si la caja completa está más lejos que el mejor actual, saltamos
    dist_caja = _dist_minima_caja(
        punto_objetivo, nodo.xmin, nodo.xmax, nodo.ymin, nodo.ymax
    )
    if mejor is not None and dist_caja >= mejor[1]:
        return mejor

    # Revisar los puntos en este nodo
    for punto in nodo.puntos:
        d = calcular_distancia(punto, punto_objetivo)
        if mejor is None or d < mejor[1]:
            mejor = (punto, d)

    # Recurrir en los hijos: primero el cuadrante donde cae el objetivo
    if nodo.dividido:
        cx = (nodo.xmin + nodo.xmax) / 2.0
        cy = (nodo.ymin + nodo.ymax) / 2.0

        # El cuadrante más probable va primero para mejorar la poda
        if punto_objetivo[0] < cx:
            if punto_objetivo[1] >= cy:
                orden = (nodo.nw, nodo.sw, nodo.ne, nodo.se)
            else:
                orden = (nodo.sw, nodo.nw, nodo.se, nodo.ne)
        else:
            if punto_objetivo[1] >= cy:
                orden = (nodo.ne, nodo.se, nodo.nw, nodo.sw)
            else:
                orden = (nodo.se, nodo.ne, nodo.sw, nodo.nw)

        for hijo in orden:
            mejor = vecino_cercano(hijo, punto_objetivo, mejor)

    return mejor


# ─────────────────────────────────────────────────────────
# Fuerza bruta (para comparación y verificación)
# ─────────────────────────────────────────────────────────

def busqueda_fuerza_bruta(lista_puntos, punto_objetivo, radio):
    """
    Revisa TODOS los puntos sin ninguna optimización.
    Siempre O(n) — referencia para comparar correctitud y tiempo.
    """
    resultados = []
    for punto in lista_puntos:
        if calcular_distancia(punto, punto_objetivo) <= radio:
            resultados.append(punto)
    return resultados


def vecino_bruta(lista_puntos, punto_objetivo):
    """
    Vecino más cercano por fuerza bruta — O(n).
    """
    mejor_punto = None
    mejor_dist  = float("inf")
    for punto in lista_puntos:
        d = calcular_distancia(punto, punto_objetivo)
        if d < mejor_dist:
            mejor_dist  = d
            mejor_punto = punto
    return mejor_punto, mejor_dist
