# Estructura-de-datos-UDEA
# Ejercicio: Modelo Entidad-Relación Hospital

Este repositorio contiene la resolución del ejercicio de modelado de datos para un sistema hospitalario, utilizando la **Notación de Barker**.

## 1. Diagrama Entidad-Relación

A continuación se presenta el modelo conceptual:

```mermaid
erDiagram
    SALA {
        string nombre_sala PK "Identificador único (#)"
        int cantidad_camas "*"
    }
    EMPLEADO {
        int numero_empleado PK "Identificador único (#)"
        string nombre "*"
        string direccion "*"
        string telefono "*"
    }
    PACIENTE {
        int numero_registro PK "Asignado al ingresar (#)"
        string nombre "*"
    }

    SALA ||--o{ EMPLEADO : "trabaja en"
    SALA ||--o{ PACIENTE : "está internado en"
