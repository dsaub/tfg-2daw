# `clear_cart`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/carrito/vaciar/`  
**Tipo:** Vista pública

## Descripción

Elimina todos los ítems del carrito de una sola vez. Cancela las reservas de stock activas antes de vaciar el carrito.

## Firma

```python
def clear_cart(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Redirecciones

Siempre redirige a `view_cart`.
