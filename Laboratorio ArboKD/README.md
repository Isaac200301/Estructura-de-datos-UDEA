# 📦 Sistema de Logística de Entregas — KD-Tree

Implementación desde cero de un **Árbol KD** para resolver consultas espaciales eficientes sobre 10.000 puntos de entrega reales de Medellín, Colombia.

## Problema

Dado un conjunto de 10.000 coordenadas de edificios (datos reales de OpenStreetMap), responder eficientemente:

- ¿Qué puntos de entrega están dentro de un radio de **500 metros** de un punto dado?
- ¿Cuál es el punto de entrega **más cercano** a una ubicación dada?

## Estructura del repositorio

```
├── KDtree.py     # Implementación del KD-Tree (K dimensiones)
├── test.py       # Pruebas unitarias + visualizaciones
├── analisis.py   # Benchmark y análisis comparativo
└── README.md
```

## Archivos

### `KDtree.py`
Contiene la implementación completa desde cero:
- `NodoKD` — nodo del árbol con soporte para K dimensiones
- `construir_arbol()` — construcción O(n log n) por mediana
- `busqueda_radio()` — range search con poda inteligente O(log n + k)
- `vecino_cercano()` — nearest-neighbor usando el árbol O(log n)
- `busqueda_fuerza_bruta()` — referencia O(n) para comparación

### `test.py`
- 8 pruebas unitarias de correctitud
- 5 puntos de consulta con radio fijo de 500 m (centro + 4 cuadrantes)
- Vista global con líneas del KD-Tree
- Zoom por cada punto mostrando vecinos, conexiones y vecino más cercano

### `analisis.py`
- Análisis del **peor caso** de fuerza bruta (radio infinito)
- Benchmark de n = 100 hasta 100.000 puntos
- Determinación empírica del **umbral** donde KD-Tree supera a fuerza bruta
- Comparación en range search y vecino más cercano

## Instalación

```bash
pip install osmnx pyproj matplotlib numpy
```

## Uso

```bash
# Pruebas y visualizaciones
python test.py

# Análisis de rendimiento
python analisis.py
```

## Datos

Los puntos de entrega se obtienen de **OpenStreetMap** usando `osmnx`: centroides de edificios de Medellín, proyectados a **EPSG:3116** (sistema métrico de Colombia) para que las distancias sean en metros reales.

## Estructura del KD-Tree

El árbol divide el espacio alternando dimensiones en cada nivel:
- Nivel 0: divide por X (líneas verticales)
- Nivel 1: divide por Y (líneas horizontales)
- Nivel k: divide por dimensión `k % K`

La **poda** en range search: si la distancia del punto de consulta al plano de corte es mayor que el radio, se descarta ese subárbol completo.

## Complejidad

| Operación | Fuerza Bruta | KD-Tree |
|---|---|---|
| Construcción | — | O(n log n) |
| Range Search | O(n) | O(log n + k) |
| Vecino cercano | O(n) | O(log n) promedio |
| Peor caso | O(n) siempre | O(n) sin poda |

## ¿A partir de qué n gana el KD-Tree?

Empíricamente (radio 500 m, datos uniformes): **≈ 1.000 – 3.000 puntos**.
El umbral exacto depende del radio y la distribución de los datos.
Ver `analisis.py` para la medición precisa con los datos del ejercicio.
