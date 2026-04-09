# `create_order_from_cart`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar pública

## Descripción

Crea un pedido (`Order`) a partir del contenido actual del carrito, descuenta el stock de cada producto y vacía el carrito. Es el núcleo de la lógica de confirmación de compra.

El proceso completo se ejecuta dentro de una transacción atómica con bloqueos de fila:

1. Verifica que el carrito no está vacío.
2. Calcula el precio de cada ítem con IVA.
3. Libera reservas expiradas.
4. Si se proporcionó una reserva de stock, la bloquea y valida que siga activa.
5. Valida que el stock disponible sea suficiente para cada producto.
6. Crea el registro `Order` y los `OrderItem` asociados.
7. Descuenta el stock de cada producto.
8. Elimina los ítems del carrito.
9. Marca la reserva como completada.
10. Si el usuario está autenticado, lanza la tarea Celery `process_purchase` de forma asíncrona.

## Firma

```python
def create_order_from_cart(
    request,
    payment_method: str,
    payment_reference: str = "",
    shipping_address=None,
    stock_reservation=None
) -> tuple[Order | None, str]:
```

## Parámetros

| Nombre              | Tipo                        | Descripción                                                     |
|---------------------|-----------------------------|-----------------------------------------------------------------|
| `request`           | `HttpRequest`               | Petición HTTP de Django.                                        |
| `payment_method`    | `str`                       | Constante de pago (`Order.PAYMENT_STRIPE` o `Order.PAYMENT_PAYPAL`). |
| `payment_reference` | `str`                       | Referencia de la transacción en la pasarela (ID de sesión Stripe, ID de pago PayPal, etc.). |
| `shipping_address`  | `ShippingAddress` o `None`  | Dirección de envío seleccionada.                                |
| `stock_reservation` | `StockReservation` o `None` | Reserva de stock a completar junto con el pedido.               |

## Retorno

Tupla `(order, error_message)`:

- Pedido creado correctamente: `(Order, "")`.
- Error (carrito vacío, stock insuficiente, reserva caducada, etc.): `(None, "mensaje de error")`.

## Uso

Llamada desde [`checkout_success`](./checkout_success.md) y [`paypal_execute`](./paypal_execute.md).

> [!IMPORTANT]
> Toda la operación se ejecuta bajo `transaction.atomic()` con `SELECT FOR UPDATE` para garantizar la integridad del stock en entornos concurrentes.
