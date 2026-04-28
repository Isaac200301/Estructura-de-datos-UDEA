# Sistema de Logística de Entregas — Quadtree

> **Curso:** Estructuras de Datos  
> **Tema:** Árboles espaciales (Quadtree) para búsqueda eficiente  
> **Ciudad:** Medellín, Colombia — datos reales de OpenStreetMap

---

## Objetivo de la práctica

Implementar desde cero un **Quadtree** para resolver de forma eficiente dos tipos de consultas espaciales sobre 10.000 puntos de entrega reales:

1. **Búsqueda por radio:** ¿Qué puntos están dentro de 500 metros de una ubicación?
2. **Vecino más cercano:** ¿Cuál es el punto más próximo a una ubicación dada?

El proyecto compara el Quadtree contra la **fuerza bruta** para:

- Medir tiempos reales de ejecución
- Identificar el **umbral** donde el Quadtree empieza a ser más rápido
- Analizar el comportamiento en el **peor caso**

> **Restricción:** No se usaron librerías de árboles externas. Todo fue implementado a mano.

---

## ¿Qué es un Quadtree?

Un Quadtree es una estructura de datos en forma de árbol que representa de forma eficiente un área espacial bidimensional. Imagina un cuadrado que representa una sección de un mapa: en un Quadtree, ese cuadrado se divide en cuatro cuadrados más pequeños e iguales (cuadrantes). Cada uno de esos cuadrantes puede subdividirse a su vez en cuatro más, y así sucesivamente.

Esta división jerárquica permite realizar consultas espaciales eficientes como encontrar todos los puntos dentro de un área determinada.

A diferencia del KD-Tree:
- No divide por ejes alternados
- Divide el espacio **geométricamente en 4 partes iguales**
- Funciona especialmente bien cuando los datos están distribuidos de forma relativamente uniforme

---

## Idea central

El Quadtree funciona así:

1. Empiezas con todo el espacio (un gran cuadrado)
2. Si hay muchos puntos en una zona → se divide en 4 cuadrantes
3. Cada cuadrante puede dividirse otra vez si se llena

---

## Estructura del repositorio

```
Laboratorio Quad-tree/
├── Quadtree.py      <- Implementación del árbol desde cero
├── test.py          <- Pruebas y visualizaciones
├── analisis.py      <- Benchmark y comparación con fuerza bruta
├── requirements.txt <- Dependencias
├── README.md
└── image/
    └── analisis_rendimiento.png
```

---

## Cómo construí el Quadtree

### 1 · `Nodo` — la unidad básica

```python
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
```

Cada nodo guarda los límites de su rectángulo (`xmin`, `xmax`, `ymin`, `ymax`), una lista de puntos (solo en nodos hoja) y cuatro hijos: `nw`, `ne`, `sw`, `se`. El flag `dividido` indica si ya fue subdividido.

---

### 2 · `construir_quadtree(puntos)`

Construyo el árbol insertando los puntos uno a uno:

1. Calculo el **bounding box** automáticamente con `min/max` de x e y, y agrego un margen de 1 unidad para evitar problemas en los bordes exactos.
2. Creo la raíz con ese bounding box.
3. Llamo a `insertar` por cada punto.

```python
def construir_quadtree(puntos):
    if not puntos:
        return None
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    raiz = Nodo(min(xs)-1, max(xs)+1, min(ys)-1, max(ys)+1)
    for p in puntos:
        insertar(raiz, p)
    return raiz
```

> **Diferencia clave con el KD-Tree:** el KD-Tree parte por la mediana (top-down); el Quadtree parte por el centro geométrico cuando un nodo se llena (bottom-up).

---

### 3 · `subdividir(nodo)`

Calculo el punto central del rectángulo y creo cuatro hijos:

```python
cx = (nodo.xmin + nodo.xmax) / 2
cy = (nodo.ymin + nodo.ymax) / 2
```

| Hijo | Rango X        | Rango Y        |
|------|----------------|----------------|
| NW   | xmin → cx      | cy → ymax      |
| NE   | cx → xmax      | cy → ymax      |
| SW   | xmin → cx      | ymin → cy      |
| SE   | cx → xmax      | ymin → cy      |

Luego redistribuyo los puntos viejos del nodo llamando `insertar` en cada hijo.

---

### 4 · `insertar(nodo, punto)`

```
¿El punto está fuera del bbox?        →  return False
¿El nodo es hoja y tiene espacio?     →  guardar aquí y return True
¿El nodo es hoja pero está lleno?     →  subdividir() + reintentar
¿El nodo ya está dividido?            →  probar los 4 hijos en orden
```

---

### 5 · `intersecta(cx, cy, r, ...)` — poda geométrica

Verifica si un círculo de búsqueda toca el rectángulo del nodo. Si no hay intersección, descarta todo el subárbol sin revisar ningún punto.

```python
def intersecta(cx, cy, r, xmin, xmax, ymin, ymax):
    px = max(xmin, min(cx, xmax))
    py = max(ymin, min(cy, ymax))
    dx = cx - px
    dy = cy - py
    return dx*dx + dy*dy <= r*r
```

Esta función es la razón por la que el Quadtree es eficiente: si el círculo de 500 m no toca un cuadrante, se descartan todos los puntos de ese cuadrante de golpe.

---

### 6 · `buscar_radio(nodo, punto, radio)`

```python
def buscar_radio(nodo, punto, radio, resultado=None):
    if not intersecta(...):   # PODA: si no hay intersección, saltar
        return resultado
    for p in nodo.puntos:     # revisar puntos del nodo actual
        if distancia(p, punto) <= radio:
            resultado.append(p)
    if nodo.dividido:         # recurrir en los 4 hijos
        buscar_radio(nodo.nw, ...)
        buscar_radio(nodo.ne, ...)
        buscar_radio(nodo.sw, ...)
        buscar_radio(nodo.se, ...)
    return resultado
```

Complejidad: **O(log n + k)** donde k = puntos encontrados.

---

### 7 · `vecino_mas_cercano(nodo, punto, mejor)`

Recorre el árbol actualizando el mejor candidato encontrado hasta el momento:

```python
def vecino_mas_cercano(nodo, punto, mejor=None):
    for p in nodo.puntos:
        d = distancia(p, punto)
        if mejor is None or d < mejor[1]:
            mejor = (p, d)
    if nodo.dividido:
        mejor = vecino_mas_cercano(nodo.nw, punto, mejor)
        mejor = vecino_mas_cercano(nodo.ne, punto, mejor)
        mejor = vecino_mas_cercano(nodo.sw, punto, mejor)
        mejor = vecino_mas_cercano(nodo.se, punto, mejor)
    return mejor
```

---

### 8 · `buscar_bruta` / `vecino_bruta`

Recorren **todos** los puntos sin ninguna optimización — O(n) siempre. Los uso para verificar que el árbol devuelve exactamente los mismos resultados.

---

### Resumen de complejidades

| Operación           | Fuerza Bruta | Quadtree          |
|---------------------|--------------|-------------------|
| Construcción        | —            | O(n log n) prom.  |
| Espacio             | O(n)         | O(n)              |
| Búsqueda por radio  | O(n)         | O(log n + k)      |
| Vecino más cercano  | O(n)         | O(log n) prom.    |

---

## Pruebas (`test.py`)

### Datos reales

Los puntos de entrega se obtienen de **OpenStreetMap** vía `osmnx`: centroides de edificios de Medellín, proyectados al sistema métrico colombiano **EPSG:3116**.

```
EPSG:4326 (lat/lon en grados)  →  EPSG:3116 (metros, Colombia)
```

### Verificaciones de correctitud

```python
# Distancia euclidiana
assert distancia((0, 0), (3, 4)) == 5.0

# KD-Tree == fuerza bruta en radio search
res1 = set(buscar_radio(qt, p, RADIO))
res2 = set(buscar_bruta(muestra, p, RADIO))
assert res1 == res2

# Mismo vecino más cercano
_, d1 = vecino_mas_cercano(qt, p)
_, d2 = vecino_bruta(muestra, p)
assert abs(d1 - d2) < 1e-6
```

### 5 puntos de consulta — radio fijo 500 m

| Zona | Descripción |
|------|-------------|
| Centro | Centroide de todos los puntos |
| NW | Zona norte-oeste |
| NE | Zona norte-este |
| SW | Zona sur-oeste |
| SE | Zona sur-este |

---

## Visualizaciones

### Vista global — Quadtree + 5 consultas

La visualización característica del Quadtree son los **rectángulos anidados**: donde hay más puntos el árbol subdivide más, generando cuadrantes pequeños. Donde hay pocos puntos los cuadrantes son grandes. Esto se diferencia claramente del KD-Tree, que muestra líneas que se extienden.

### Zoom por punto de consulta

En el zoom se ven los rectángulos de subdivisión dentro del radio de búsqueda, las conexiones de cada vecino al punto central, y la línea al vecino más cercano.

---

## ⚡ Análisis comparativo — Quadtree vs Fuerza Bruta

![Análisis de rendimiento](image/analisis_rendimiento.png)

Para este análisis quería responder una pregunta concreta: **¿a partir de cuántos puntos el Quadtree realmente vale la pena frente a simplemente recorrer la lista?**

Lo que hice fue medir el tiempo promedio de 10 consultas aleatorias con radio de 500 m para distintos tamaños de datos (desde 100 hasta 10.000 puntos) y compararlo con la fuerza bruta.

---

### Gráfico 1 — Búsqueda por radio (500 m)

Este gráfico muestra lo más importante del ejercicio. La línea gris es la fuerza bruta y la azul es el Quadtree.

Se puede ver claramente que la fuerza bruta crece de forma casi perfectamente lineal (como se esperaba siendo O(n)), mientras que el Quadtree se mantiene casi constante. A n=10.000 la fuerza bruta tardó ~1.5 ms por consulta y el Quadtree solo ~0.05 ms — es decir, **el Quadtree fue ~29 veces más rápido**.

La línea gris punteada muestra el tiempo de construcción del árbol, que se paga una sola vez. Esto tiene sentido para datos estáticos como en este ejercicio: se construye el árbol al inicio y luego se hacen miles de consultas baratas.

| n | Fuerza Bruta | Quadtree | Speedup |
|---|---|---|---|
| 100 | 0.013 ms | 0.011 ms | 1.2× |
| 500 | 0.058 ms | 0.019 ms | 3.1× |
| 1.000 | 0.125 ms | 0.020 ms | 6.2× |
| 5.000 | 0.600 ms | 0.040 ms | 15.1× |
| 10.000 | 1.528 ms | 0.053 ms | 29.0× |

**¿Por qué el Quadtree es tan rápido con radio pequeño?** Porque cuando el círculo de búsqueda (500 m) es pequeño relativo al espacio total (~20 km × 20 km), la función `intersecta()` descarta los cuatro hijos de la mayoría de los nodos sin siquiera revisar sus puntos. El árbol poda ramas enteras del espacio de golpe.

---

### Gráfico 2 — Vecino más cercano

Para la búsqueda del vecino más cercano el comportamiento es similar: el Quadtree gana desde tamaños relativamente pequeños. Aquí la función recorre el árbol actualizando el mejor candidato, pero sin la poda por distancia mínima al bbox que tendría una implementación más avanzada. Aun así, la estructura jerárquica ayuda a llegar rápido a las zonas más prometedoras.

---

### Gráfico 3 — Peor caso

Este fue el gráfico más interesante porque muestra algo contra-intuitivo: **con radio infinito, la fuerza bruta puede ser más rápida que el Quadtree**.

¿Por qué? Porque con un radio que cubre todo el espacio, el Quadtree no puede podar ningún nodo — tiene que visitar todos los nodos internos (con 4 hijos cada uno) y revisar todos los puntos en cada hoja. Eso es O(n) igual que la fuerza bruta, pero con el overhead de la recursión sobre la estructura del árbol.

La fuerza bruta en cambio es O(n) puro: un solo bucle sin overhead de ningún tipo. Esto me hizo entender que el Quadtree no es mejor en todos los casos — su ventaja depende de que el radio sea **pequeño relativo al espacio total**.

---

### ¿A partir de qué n gana el Quadtree?

Empíricamente, con radio 500 m sobre un espacio de 20 km × 20 km, el Quadtree empieza a ser más rápido a partir de unos **200–500 puntos**. Esto se debe a que la poda geométrica es muy efectiva para radios pequeños: incluso con pocos puntos, la mayoría del espacio queda fuera del radio y el árbol lo descarta.

La ventaja **crece con n** porque la fuerza bruta siempre revisa los n puntos sin importar nada, mientras que el Quadtree revisa un número casi constante de nodos para radios pequeños.

> **Conclusión:** Implementar el Quadtree desde cero me ayudó a entender por qué las estructuras de datos espaciales existen. Con 10.000 puntos y muchas consultas por día, la diferencia de 29× se vuelve enorme a escala real. Además, la visualización de rectángulos anidados me pareció muy intuitiva para entender cómo el árbol organiza el espacio según la densidad de puntos.

---

## Instalación

```bash
pip install -r requirements.txt
```

```bash
# Pruebas y visualizaciones
python test.py

# Análisis de rendimiento
python analisis.py
```

---

## Referencia

- Claude para la comstruccion de las graficas y los mapas
- OpenStreetMap contributors (2024). Datos cartográficos de Medellín, Colombia.
