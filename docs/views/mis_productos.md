# `mis_productos`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/venta/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Muestra el panel de vendedor con la lista de todos los productos creados por el usuario autenticado. Accesible desde el botón "Panel Vendedor" en la cabecera.

## Firma

```python
def mis_productos(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable          | Tipo      | Descripción                                          |
|-------------------|-----------|------------------------------------------------------|
| `productos`       | QuerySet  | Productos del usuario con categoría e imagen principal precargados. |
| `total_productos` | `int`     | Número total de productos del vendedor.              |

## Template

`tienda/mis_productos.html`
