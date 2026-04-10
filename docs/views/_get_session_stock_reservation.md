# `_get_session_stock_reservation`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Recupera la reserva de stock almacenada en la sesión del usuario, validando que siga activa, no haya caducado y corresponda al método de pago indicado.

## Firma

```python
def _get_session_stock_reservation(
    request: HttpRequest,
    payment_method: str
) -> StockReservation | None:
```

## Parámetros

| Nombre           | Tipo          | Descripción                                        |
|------------------|---------------|----------------------------------------------------|
| `request`        | `HttpRequest` | Petición HTTP de Django.                           |
| `payment_method` | `str`         | Método de pago esperado (`stripe` o `paypal`).     |

## Retorno

La instancia `StockReservation` activa si existe y es válida, o `None` si la sesión no tiene reserva, el método de pago no coincide o la reserva ha caducado.

## Uso interno

Llamada desde [`checkout_success`](./checkout_success.md) y [`paypal_execute`](./paypal_execute.md) para recuperar la reserva antes de confirmar el pedido.
