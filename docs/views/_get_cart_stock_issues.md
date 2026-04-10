# `_get_cart_stock_issues`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Comprueba si alguno de los ítems del carrito supera el stock disponible y devuelve la lista de conflictos encontrados.

Para cada ítem, compara la cantidad solicitada con el stock disponible obtenido mediante [`_get_available_stock_by_product`](./_get_available_stock_by_product.md). Si la cantidad supera el disponible, se añade un objeto de issue a la lista de resultado.

## Firma

```python
def _get_cart_stock_issues(
    cart_items,
    exclude_reservation_ids=None
) -> list[dict]:
```

## Parámetros

| Nombre                    | Tipo             | Descripción                                         |
|---------------------------|------------------|-----------------------------------------------------|
| `cart_items`              | lista de `CartItem` | Ítems del carrito a verificar.                   |
| `exclude_reservation_ids` | lista de `int` o `None` | Reservas a excluir del cómputo de stock reservado. |

## Retorno

Lista de diccionarios con la estructura:

```python
{
    "product_name": str,  # Nombre del producto con conflicto
    "requested": int,     # Cantidad solicitada
    "available": int,     # Cantidad disponible
}
```

Lista vacía si no hay problemas de stock.

## Uso interno

Llamada en [`view_cart`](./view_cart.md) y [`checkout`](./checkout.md) para mostrar avisos al usuario, y en [`create_checkout_session`](./create_checkout_session.md) y [`create_paypal_payment`](./create_paypal_payment.md) para bloquear el pago si hay problemas.
