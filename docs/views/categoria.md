# `categoria`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/categoria/<id>/`  
**Tipo:** Vista pública

## Descripción

Muestra el catálogo paginado de productos filtrados por categoría. Reutiliza el template `tienda/index.html` para mostrar los resultados.

## Firma

```python
def categoria(request: HttpRequest, id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción                    |
|-----------|---------------|--------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.       |
| `id`      | `int`         | Identificador de la categoría. |

## Parámetros GET

| Parámetro | Tipo  | Por defecto | Descripción                 |
|-----------|-------|-------------|-----------------------------|
| `page`    | `int` | `1`         | Número de página a mostrar. |

## Contexto del template

| Variable     | Tipo      | Descripción                                          |
|--------------|-----------|------------------------------------------------------|
| `products`   | QuerySet  | Productos de la categoría en la página actual.       |
| `categories` | QuerySet  | Todas las categorías para el menú de navegación.     |

## Template

`tienda/index.html`
