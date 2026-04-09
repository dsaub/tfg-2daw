# `search`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/buscar/`  
**Tipo:** Vista pública

## Descripción

Busca productos por nombre, descripción breve o descripción completa y devuelve los resultados. Si no se proporciona ningún término de búsqueda, se devuelve una lista vacía.

## Firma

```python
def search(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Parámetros GET

| Parámetro | Tipo   | Descripción                  |
|-----------|--------|------------------------------|
| `q`       | `str`  | Término de búsqueda.         |

## Contexto del template

| Variable     | Tipo      | Descripción                                        |
|--------------|-----------|----------------------------------------------------|
| `products`   | QuerySet o lista | Resultados de la búsqueda.                  |
| `query`      | `str`     | Término de búsqueda utilizado.                     |
| `categories` | QuerySet  | Todas las categorías para el menú de navegación.   |

## Template

`tienda/search.html`
