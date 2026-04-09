# `update_cart_item`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/carrito/actualizar/<item_id>/`  
**Tipo:** Vista pública

## Descripción

Actualiza la cantidad de un ítem del carrito.

- Si la nueva cantidad es mayor que cero, actualiza el registro.
- Si la nueva cantidad es cero o menor, elimina el ítem del carrito.
- Valida que la cantidad no supere el stock disponible.
- Cancela las reservas de stock activas antes de modificar el carrito.

## Firma

```python
def update_cart_item(request: HttpRequest, item_id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción                       |
|-----------|---------------|-----------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.          |
| `item_id` | `int`         | ID del `CartItem` a actualizar.   |

## Parámetros POST

| Campo      | Tipo  | Por defecto | Descripción           |
|------------|-------|-------------|-----------------------|
| `quantity` | `int` | `1`         | Nueva cantidad.       |

## Redirecciones

Siempre redirige a `view_cart`.
