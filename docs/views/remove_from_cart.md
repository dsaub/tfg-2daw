# `remove_from_cart`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/carrito/eliminar/<item_id>/`  
**Tipo:** Vista pública

## Descripción

Elimina un ítem específico del carrito. Cancela las reservas de stock activas antes de eliminar el ítem, para que el stock quede libre inmediatamente.

## Firma

```python
def remove_from_cart(request: HttpRequest, item_id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción                     |
|-----------|---------------|---------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.        |
| `item_id` | `int`         | ID del `CartItem` a eliminar.   |

## Redirecciones

Siempre redirige a `view_cart`.
