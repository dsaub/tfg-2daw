# `get_price_with_vat_decimal`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar pública

## Descripción

Calcula el precio de un producto con el IVA incluido y lo devuelve redondeado a dos decimales usando la regla de redondeo `ROUND_HALF_UP`.

La tasa de IVA se toma de `VAT_RATE` definida en `tienda/vars.py`.

## Firma

```python
def get_price_with_vat_decimal(price) -> Decimal:
```

## Parámetros

| Nombre  | Tipo                        | Descripción                         |
|---------|-----------------------------|-------------------------------------|
| `price` | `float`, `int` o `Decimal`  | Precio base del producto sin IVA.   |

## Retorno

`Decimal` con el precio final (base + IVA) redondeado a dos decimales.

## Ejemplo

```python
# Suponiendo VAT_RATE = 0.21
get_price_with_vat_decimal(10.00)  # → Decimal('12.10')
```

## Uso

Llamada desde [`create_order_from_cart`](./create_order_from_cart.md), [`create_checkout_session`](./create_checkout_session.md) y [`create_paypal_payment`](./create_paypal_payment.md) para calcular el importe correcto a cobrar al cliente.

> [!NOTE]
> Se utiliza `Decimal` para evitar errores de precisión en operaciones de punto flotante propios de los cálculos monetarios.
