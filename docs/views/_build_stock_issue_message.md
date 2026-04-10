# `_build_stock_issue_message`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Construye el mensaje de error legible por el usuario cuando hay un conflicto de stock para un ítem del carrito.

## Firma

```python
def _build_stock_issue_message(issue: dict) -> str:
```

## Parámetros

| Nombre  | Tipo   | Descripción                                                                      |
|---------|--------|----------------------------------------------------------------------------------|
| `issue` | `dict` | Diccionario con las claves `product_name`, `available` y `requested`.            |

## Retorno

Cadena con el mensaje de error, por ejemplo:

> `No hay stock suficiente de 'Camiseta azul'. Disponible: 3, solicitado: 5.`

## Uso interno

Llamada en [`_create_stock_reservation_for_cart`](./_create_stock_reservation_for_cart.md), [`create_order_from_cart`](./create_order_from_cart.md), [`create_checkout_session`](./create_checkout_session.md) y [`create_paypal_payment`](./create_paypal_payment.md).
