# `_create_stock_reservation_for_cart`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Crea atómicamente una reserva de stock para todos los ítems del carrito, bloqueando el inventario durante el proceso de pago.

El proceso es:

1. Libera reservas expiradas.
2. Dentro de una transacción atómica con bloqueo (`SELECT FOR UPDATE`), cancela la reserva activa previa del usuario.
3. Verifica la disponibilidad de stock para cada producto.
4. Si todo está disponible, crea un registro `StockReservation` con los `StockReservationItem` asociados, con una caducidad de `STOCK_RESERVATION_MINUTES` minutos.

## Firma

```python
def _create_stock_reservation_for_cart(
    request: HttpRequest,
    cart_items,
    payment_method: str
) -> tuple[StockReservation | None, list[str]]:
```

## Parámetros

| Nombre           | Tipo                  | Descripción                             |
|------------------|-----------------------|-----------------------------------------|
| `request`        | `HttpRequest`         | Petición HTTP de Django.                |
| `cart_items`     | lista de `CartItem`   | Ítems del carrito a reservar.           |
| `payment_method` | `str`                 | Método de pago (`stripe` o `paypal`).   |

## Retorno

Tupla `(reserva, errores)`:

- Si la reserva se crea con éxito: `(StockReservation, [])`.
- Si hay problemas de stock o el carrito está vacío: `(None, [mensaje_error])`.

## Uso interno

Llamada desde [`create_checkout_session`](./create_checkout_session.md) y [`create_paypal_payment`](./create_paypal_payment.md) justo antes de redirigir al usuario a la pasarela de pago.

> [!IMPORTANT]
> La operación se ejecuta dentro de una transacción con bloqueos de fila para evitar condiciones de carrera en entornos con alta concurrencia.
