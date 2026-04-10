# `_clear_stock_reservation_session`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Elimina de la sesión HTTP las claves relacionadas con la reserva de stock actual:
- `STOCK_RESERVATION_SESSION_KEY` → ID de la reserva activa.
- `STOCK_RESERVATION_PAYMENT_SESSION_KEY` → Método de pago de la reserva.

## Firma

```python
def _clear_stock_reservation_session(request: HttpRequest) -> None:
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Retorno

No devuelve ningún valor.

## Uso interno

Llamada tras completar o cancelar el proceso de pago para limpiar el estado de sesión. Usada en [`add_to_cart`](./add_to_cart.md), [`update_cart_item`](./update_cart_item.md), [`remove_from_cart`](./remove_from_cart.md), [`clear_cart`](./clear_cart.md), [`checkout_success`](./checkout_success.md), [`checkout_cancel`](./checkout_cancel.md) y [`paypal_execute`](./paypal_execute.md).
