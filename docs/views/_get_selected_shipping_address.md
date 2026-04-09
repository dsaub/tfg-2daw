# `_get_selected_shipping_address`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Obtiene la dirección de envío seleccionada por el usuario durante el proceso de pago, validando que pertenezca al usuario autenticado.

Intenta leer `shipping_address_id` en el siguiente orden:
1. Parámetro `POST` del formulario.
2. Cuerpo JSON de la petición (para peticiones AJAX/API).

Si el ID no se encuentra o no corresponde al usuario actual, devuelve `None`.

## Firma

```python
def _get_selected_shipping_address(request: HttpRequest) -> ShippingAddress | None:
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Retorno

Instancia de `ShippingAddress` perteneciente al usuario, o `None` si no se encontró o no es válida.

## Uso interno

Llamada desde [`create_checkout_session`](./create_checkout_session.md) y [`create_paypal_payment`](./create_paypal_payment.md).

> [!CAUTION]
> La validación `user=request.user` es crítica para la seguridad. Nunca omitas este filtro, ya que evita que un usuario use la dirección de otro.
