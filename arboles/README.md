# 🌳 Árboles — Medición de Tiempos de Búsqueda

Curso: Estructura de Datos — Universidad de Antioquia  

---

## 📋 Descripción

Este módulo implementa y compara tres estructuras de datos para almacenar y buscar registros de estudiantes: una **lista enlazada**, un **Árbol Binario de Búsqueda (ABB)** y un **Árbol B+**. El objetivo principal es medir y comparar el tiempo de búsqueda por ID en cada estructura usando 10.000 registros de estudiantes generados aleatoriamente.

---

## 📁 Contenido

| Archivo | Descripción |
|---|---|
| `Tiempos_Arboles.ipynb` | Notebook principal con la implementación completa y los benchmarks |

---

## 🗂️ Estructura del Notebook

### 1. Generación de datos
Se generan **10.000 estudiantes** con los siguientes campos:

| Campo | Tipo | Rango |
|---|---|---|
| `id` | Entero | 0 – 9999 (aleatorio, sin orden) |
| `nombre` | String | Seleccionado de una lista de 15 nombres |
| `edad` | Entero | 16 – 30 años |
| `promedio` | Float | 0.0 – 5.0 (una decimal) |

Los IDs se generan con `random.shuffle()` para que estén **desordenados**, lo cual es esencial para que el árbol ABB quede balanceado y no degenere en una lista lineal.

---

### 2. Búsqueda en Lista
Recorre los estudiantes uno por uno comparando el `id` hasta encontrar el buscado.
```
Complejidad: O(n)
Peor caso: recorre los 10.000 registros completos
```

---

### 3. Árbol Binario de Búsqueda (ABB)
Cada nodo del árbol almacena un estudiante. La regla es:
- IDs **menores** van al subárbol **izquierdo**
- IDs **mayores** van al subárbol **derecho**

La inserción y búsqueda son **iterativas** (con `while`) para evitar el `RecursionError` que ocurre con datos secuenciales en Python.
```
Complejidad: O(log n) en un árbol balanceado
```

---

### 4. Árbol B+
Implementación simplificada basada en **páginas** (bloques de 50 estudiantes cada una) y un **índice plano** con el ID mínimo de cada página.

La búsqueda se realiza en dos pasos usando `bisect` (búsqueda binaria nativa de Python):
1. Búsqueda binaria en el índice → determina en qué página está el ID
2. Búsqueda binaria dentro de la página → encuentra el registro exacto
```
Complejidad: O(log n) con doble búsqueda binaria
Ventaja extra: las páginas están enlazadas, lo que permite recorridos secuenciales eficientes
```

---

### 5. Benchmarks
Se ejecutan **100.000 búsquedas** por cada estructura usando los mismos IDs aleatorios para garantizar una comparación justa. Se usa `time.process_time()` para medir únicamente el tiempo de CPU, sin incluir tiempos de espera del sistema.

#### Resultados esperados (aproximados)

| Estructura | Tiempo total (100k búsquedas) | Tiempo promedio por búsqueda |
|---|---|---|
| Lista | ~30 – 60 s | ~0.0003 s |
| ABB | ~0.5 – 1 s | ~0.000005 s |
| B+ | ~0.1 – 0.3 s | ~0.000001 s |

> ⚠️ Los tiempos varían según los recursos de la sesión de Colab en el momento de ejecución.

---

## ⚙️ Cómo ejecutar

1. Abre `Tiempos_Arboles.ipynb` en [Google Colab](https://colab.research.google.com/)
2. Ve a **Entorno de ejecución → Ejecutar todo**
3. Los resultados del benchmark aparecen al final del notebook

No requiere instalar librerías externas. Solo usa módulos estándar de Python: `random`, `time` y `bisect`.

---

## 📊 Conclusión

| Criterio | Lista | ABB | B+ |
|---|---|---|---|
| Velocidad de búsqueda | ❌ Lenta O(n) | ✅ Rápida O(log n) | ✅✅ Muy rápida O(log n) |
| Memoria | ✅ Mínima | ⚠️ Media | ⚠️ Media |
| Facilidad de implementación | ✅ Simple | ⚠️ Media | ❌ Compleja |
| Recorrido secuencial | ❌ Desordenado | ⚠️ Inorden | ✅ Lista enlazada |

El **Árbol B+** es la estructura más eficiente para búsquedas, razón por la cual es usada internamente por motores de bases de datos como MySQL y PostgreSQL.
