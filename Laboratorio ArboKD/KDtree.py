"""
KDtree.py
=========
Implementación desde cero de un Árbol KD para K dimensiones.

Estructura del módulo:
    - NodoKD           : nodo del árbol
    - construir_arbol  : construcción O(n log n)
    - busqueda_radio   : range search con poda inteligente
    - vecino_cercano   : nearest-neighbor usando el árbol (no fuerza bruta)
    - calcular_distancia: distancia euclidiana en K dimensiones
"""

import math


# ──────────────────────────────────────────────
# Nodo del árbol
# ──────────────────────────────────────────────

class NodoKD:
    """
    Nodo de un KD-Tree.

    Atributos:
        punto     : tupla de K coordenadas  (x1, x2, ..., xk)
        izquierda : subárbol izquierdo (puntos menores en el eje actual)
        derecha   : subárbol derecho   (puntos mayores en el eje actual)
        eje       : dimensión por la que se dividió en este nivel
    """

    def __init__(self, punto, izquierda=None, derecha=None, eje=0):
        self.punto = punto
        self.izquierda = izquierda
        self.derecha = derecha
        self.eje = eje

    def __repr__(self):
        return f"NodoKD(punto={self.punto}, eje={self.eje})"


# ──────────────────────────────────────────────
# Distancia euclidiana (K dimensiones)
# ──────────────────────────────────────────────

def calcular_distancia(punto_a, punto_b):
    """
    Distancia euclidiana entre dos puntos de K dimensiones.

    Funciona para cualquier K:
        d = sqrt( sum( (a_i - b_i)^2 ) )

    Parámetros:
        punto_a, punto_b : tuplas o listas de misma longitud K

    Retorna:
        distancia (float) en las mismas unidades que los puntos
    """
    if len(punto_a) != len(punto_b):
        raise ValueError(
            f"Los puntos tienen dimensiones distintas: {len(punto_a)} vs {len(punto_b)}"
        )
    suma = sum((a - b) ** 2 for a, b in zip(punto_a, punto_b))
    return math.sqrt(suma)


# ──────────────────────────────────────────────
# Construcción del árbol
# ──────────────────────────────────────────────

def construir_arbol(lista_puntos, profundidad=0):
    """
    Construye un KD-Tree de forma recursiva.

    Estrategia: mediana como pivote → árbol balanceado.
    El eje de división alterna cíclicamente entre las K dimensiones.

    Complejidad:
        Tiempo : O(n log n)   (sort en cada nivel)
        Espacio: O(n)         (un nodo por punto)

    Parámetros:
        lista_puntos : lista de tuplas con K coordenadas
        profundidad  : nivel actual (controla qué eje usar)

    Retorna:
        NodoKD raíz del subárbol, o None si la lista está vacía
    """
    if not lista_puntos:
        return None

    # K se infiere automáticamente de los datos → soporta cualquier dimensión
    k = len(lista_puntos[0])
    eje = profundidad % k

    # Ordenar por el eje actual y tomar la mediana como pivote
    lista_puntos = sorted(lista_puntos, key=lambda p: p[eje])
    indice_mediana = len(lista_puntos) // 2

    return NodoKD(
        punto=lista_puntos[indice_mediana],
        izquierda=construir_arbol(
            lista_puntos[:indice_mediana], profundidad + 1
        ),
        derecha=construir_arbol(
            lista_puntos[indice_mediana + 1 :], profundidad + 1
        ),
        eje=eje,
    )


# ──────────────────────────────────────────────
# Búsqueda por radio (Range Search)
# ──────────────────────────────────────────────

def busqueda_radio(nodo, punto_objetivo, radio, resultados=None):
    """
    Encuentra todos los puntos del árbol dentro de `radio` unidades
    del `punto_objetivo`.

    Algoritmo:
        1. Revisar el nodo actual → añadir si está dentro del radio
        2. Ir al subárbol del lado donde cae el punto objetivo
        3. Poda: solo explorar el otro subárbol si el plano de división
           está a menos de `radio` unidades (puede haber puntos allí)

    Complejidad promedio: O(log n + k)
        donde k = número de puntos encontrados

    Parámetros:
        nodo           : nodo actual del árbol (NodoKD o None)
        punto_objetivo : tupla de K coordenadas del punto de consulta
        radio          : distancia máxima (en las mismas unidades del árbol)
        resultados     : lista acumuladora (se crea en la primera llamada)

    Retorna:
        lista de puntos (tuplas) dentro del radio
    """
    if resultados is None:
        resultados = []

    if nodo is None:
        return resultados

    # 1. ¿El nodo actual está dentro del radio?
    distancia = calcular_distancia(nodo.punto, punto_objetivo)
    if distancia <= radio:
        resultados.append(nodo.punto)

    # 2. Decidir qué lado explorar primero
    eje = nodo.eje
    diferencia_eje = punto_objetivo[eje] - nodo.punto[eje]

    lado_cercano = nodo.izquierda if diferencia_eje <= 0 else nodo.derecha
    lado_lejano  = nodo.derecha   if diferencia_eje <= 0 else nodo.izquierda

    # Siempre ir al lado donde cae el punto objetivo
    busqueda_radio(lado_cercano, punto_objetivo, radio, resultados)

    # 3. PODA: solo cruzar el plano si la distancia perpendicular <= radio
    #    |diferencia_eje| es la distancia del punto objetivo al plano de corte
    if abs(diferencia_eje) <= radio:
        busqueda_radio(lado_lejano, punto_objetivo, radio, resultados)

    return resultados


# ──────────────────────────────────────────────
# Vecino más cercano (usando el árbol)
# ──────────────────────────────────────────────

def vecino_cercano(nodo, punto_objetivo, mejor=None):
    """
    Encuentra el punto más cercano al `punto_objetivo` usando el KD-Tree.

    IMPORTANTE: Esta función usa el árbol para descartar regiones imposibles
    en cada paso, logrando O(log n) en promedio — a diferencia de buscar
    linealmente en los resultados del range search.

    Algoritmo:
        1. Ir hacia la hoja más probable (lado donde cae el objetivo)
        2. Al regresar, actualizar el mejor candidato
        3. Solo explorar el otro lado si podría contener algo más cercano
           (distancia al plano de corte < mejor distancia actual)

    Parámetros:
        nodo           : nodo actual (NodoKD o None)
        punto_objetivo : tupla de K coordenadas
        mejor          : tupla (punto, distancia) del mejor encontrado hasta ahora

    Retorna:
        (punto_mas_cercano, distancia_minima)
    """
    if nodo is None:
        return mejor

    distancia_actual = calcular_distancia(nodo.punto, punto_objetivo)

    # Actualizar el mejor si encontramos algo más cercano
    if mejor is None or distancia_actual < mejor[1]:
        mejor = (nodo.punto, distancia_actual)

    eje = nodo.eje
    diferencia_eje = punto_objetivo[eje] - nodo.punto[eje]

    # Decidir qué lado explorar primero (el más probable)
    lado_cercano = nodo.izquierda if diferencia_eje <= 0 else nodo.derecha
    lado_lejano  = nodo.derecha   if diferencia_eje <= 0 else nodo.izquierda

    # Ir al lado cercano primero
    mejor = vecino_cercano(lado_cercano, punto_objetivo, mejor)

    # Solo cruzar al otro lado si el plano de corte está más cerca
    # que la mejor distancia encontrada hasta ahora
    if abs(diferencia_eje) < mejor[1]:
        mejor = vecino_cercano(lado_lejano, punto_objetivo, mejor)

    return mejor


# ──────────────────────────────────────────────
# Fuerza bruta (para comparación)
# ──────────────────────────────────────────────

def busqueda_fuerza_bruta(lista_puntos, punto_objetivo, radio):
    """
    Revisa TODOS los puntos sin ninguna optimización.

    Siempre O(n) — útil para verificar correctitud y medir rendimiento.

    Parámetros:
        lista_puntos   : lista de tuplas con K coordenadas
        punto_objetivo : punto de consulta
        radio          : distancia máxima

    Retorna:
        lista de puntos dentro del radio
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
    mejor_dist = float("inf")
    for punto in lista_puntos:
        d = calcular_distancia(punto, punto_objetivo)
        if d < mejor_dist:
            mejor_dist = d
            mejor_punto = punto
    return mejor_punto, mejor_dist
