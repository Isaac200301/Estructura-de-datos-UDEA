# Sistema de Logística de Entregas — Quadtree

> **Curso:** Estructuras de Datos  
> **Tema:** Árboles espaciales (Quadtree) para búsqueda eficiente  
> **Ciudad:** Medellín, Colombia — datos reales de OpenStreetMap

---

##  Objetivo de la práctica

Implementar desde cero un **Quadtree** para resolver de forma eficiente dos tipos de consultas espaciales sobre 10.000 puntos de entrega:

1. **Búsqueda por radio:** ¿Qué puntos están dentro de 500 metros de una ubicación?
2. **Vecino más cercano:** ¿Cuál es el punto más próximo?

El proyecto compara el Quadtree contra la **fuerza bruta** para:

- Medir tiempos reales de ejecución  
- Identificar el **umbral** donde el Quadtree empieza a ser mejor  
- Analizar el comportamiento en el **peor caso**

---

##  ¿Qué es un Quadtree?

Un Quadtree es una estructura de datos en forma de árbol que se utiliza en informática para representar de forma eficiente un área espacial bidimensional. Imagina un cuadrado que representa una sección de un mapa. En un Quadtree, este cuadrado se divide en cuatro cuadrados más pequeños e iguales (o «cuadrantes»). Cada uno de estos cuadrantes se puede subdividir a su vez en cuatro cuadrados más pequeños, y así sucesivamente. Esta división jerárquica permite realizar consultas espaciales eficientes, como encontrar todos los puntos dentro de un área determinada.

A diferencia del KD-Tree:
- No divide por ejes alternados
- Divide el espacio **geométricamente en 4 partes iguales**

---

## Idea central

El Quadtree funciona así:

1. Empiezas con todo el espacio (un gran cuadrado)
2. Si hay muchos puntos en una zona:
   → se divide en 4 cuadrantes
3. Cada cuadrante puede dividirse otra vez si se llena

---
<img width="1440" height="2840" alt="image" src="https://github.com/user-attachments/assets/8d80445e-91de-4acf-8d4e-58eb016c4c6b" />
