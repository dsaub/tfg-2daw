# `_cancel_active_stock_reservations_for_request`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Cancela todas las reservas de stock activas y no caducadas asociadas al usuario o sesión actual. Antes de cancelar, llama a [`_release_expired_stock_reservations`](./_release_expired_stock_reservations.md) para que el estado de las reservas sea consistente.

## Firma

```python
def _cancel_active_stock_reservations_for_request(request: HttpRequest) -> None:
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Retorno

No devuelve ningún valor.

## Uso interno

Llamada cuando el usuario modifica el carrito (agrega, actualiza o elimina un ítem, o lo vacía por completo), garantizando que cualquier reserva de stock previa quede liberada antes de la nueva operación. Usada en [`add_to_cart`](./add_to_cart.md), [`update_cart_item`](./update_cart_item.md), [`remove_from_cart`](./remove_from_cart.md), [`clear_cart`](./clear_cart.md) y [`checkout_cancel`](./checkout_cancel.md).
