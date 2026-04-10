# `_get_reserved_quantities_by_product`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Calcula la cantidad total de stock reservada activamente para un conjunto de productos, excluyendo opcionalmente ciertas reservas.

Consulta `StockReservationItem` para encontrar todas las reservas activas y no caducadas, agrupa por producto y suma las cantidades.

## Firma

```python
def _get_reserved_quantities_by_product(
    product_ids,
    exclude_reservation_ids=None
) -> dict:
```

## Parámetros

| Nombre                    | Tipo             | Descripción                                                      |
|---------------------------|------------------|------------------------------------------------------------------|
| `product_ids`             | lista de `int`   | IDs de los productos a consultar.                                |
| `exclude_reservation_ids` | lista de `int` o `None` | IDs de reservas a excluir del cómputo (por ejemplo, la reserva propia del usuario que está finalizando el pago). |

## Retorno

Diccionario `{product_id: total_reserved}`. Si `product_ids` está vacío devuelve `{}`.

## Uso interno

Utilizada en [`_get_available_stock_by_product`](./_get_available_stock_by_product.md) y [`_create_stock_reservation_for_cart`](./_create_stock_reservation_for_cart.md).
