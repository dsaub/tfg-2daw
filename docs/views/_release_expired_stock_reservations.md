# `_release_expired_stock_reservations`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Marca como expiradas (`STATUS_EXPIRED`) todas las reservas de stock activas cuya fecha de caducidad (`expires_at`) haya pasado. Se ejecuta como paso previo a cualquier operación que lea o modifique reservas, garantizando que el inventario virtual refleje la realidad.

## Firma

```python
def _release_expired_stock_reservations() -> None:
```

## Retorno

No devuelve ningún valor.

## Uso interno

Llamada al inicio de [`_cancel_active_stock_reservations_for_request`](./_cancel_active_stock_reservations_for_request.md), [`_get_reserved_quantities_by_product`](./_get_reserved_quantities_by_product.md) (indirectamente), [`_get_active_reservation_ids_for_request`](./_get_active_reservation_ids_for_request.md), [`_get_available_stock_by_product`](./_get_available_stock_by_product.md) y [`create_order_from_cart`](./create_order_from_cart.md).

> [!NOTE]
> Esta función realiza una actualización masiva en la base de datos (`bulk update`). No envía señales individuales de Django por reserva.
