# `home`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/`  
**Tipo:** Vista pública

## Descripción

Renderiza la página de inicio de la tienda. Muestra una selección de productos destacados (los 8 más recientes por ID), todas las categorías disponibles y estadísticas generales como el total de productos y el número de vendedores activos.

## Firma

```python
def home(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable           | Tipo        | Descripción                                              |
|--------------------|-------------|----------------------------------------------------------|
| `featured_products` | QuerySet   | Últimos 8 productos ordenados por ID descendente.        |
| `categories`        | QuerySet   | Todas las categorías disponibles.                        |
| `total_products`    | `int`      | Número total de productos en la tienda.                  |
| `total_sellers`     | `int`      | Número de usuarios que tienen al menos un producto creado. |

## Template

`tienda/home.html`
