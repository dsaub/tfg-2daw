# `_get_available_stock_by_product`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Calcula el stock disponible real de cada producto, descontando las cantidades reservadas por otras reservas activas.

El stock disponible se calcula como:

```
disponible = max(stock_total - cantidades_reservadas, 0)
```

Antes de calcular, libera las reservas expiradas llamando a [`_release_expired_stock_reservations`](./_release_expired_stock_reservations.md).

## Firma

```python
def _get_available_stock_by_product(
    product_ids,
    exclude_reservation_ids=None
) -> dict:
```

## Parámetros

| Nombre                    | Tipo             | Descripción                                                                  |
|---------------------------|------------------|------------------------------------------------------------------------------|
| `product_ids`             | lista de `int`   | IDs de los productos a consultar.                                            |
| `exclude_reservation_ids` | lista de `int` o `None` | Reservas a excluir del cómputo (habitualmente, la reserva activa propia del usuario). |

## Retorno

Diccionario `{product_id: stock_disponible}`.

## Uso interno

Llamada desde [`add_to_cart`](./add_to_cart.md), [`update_cart_item`](./update_cart_item.md) y [`_get_cart_stock_issues`](./_get_cart_stock_issues.md).
