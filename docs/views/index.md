# `index`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/productos/`  
**Tipo:** Vista pública

## Descripción

Muestra el catálogo paginado de productos. El tamaño de página se controla con la constante `PAGE_SIZE` definida en `tienda/vars.py`.

## Firma

```python
def index(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Parámetros GET

| Parámetro | Tipo  | Por defecto | Descripción          |
|-----------|-------|-------------|----------------------|
| `page`    | `int` | `1`         | Número de página a mostrar. |

## Contexto del template

| Variable     | Tipo      | Descripción                                       |
|--------------|-----------|---------------------------------------------------|
| `products`   | QuerySet  | Productos de la página actual (slice de la BD).   |
| `categories` | QuerySet  | Todas las categorías para el menú de navegación.  |

## Template

`tienda/index.html`
