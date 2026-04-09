# `create_paypal_payment`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/paypal/crear/`  
**Tipo:** Vista privada (requiere autenticación)  
**Método HTTP:** Solo `POST`  
**Decorador:** `@login_required`

## Descripción

Crea un pago en PayPal y devuelve la URL de aprobación al frontend para redirigir al usuario. Sigue un flujo similar a [`create_checkout_session`](./create_checkout_session.md) pero usando la SDK de PayPal REST.

El proceso es:

1. Obtiene y valida la dirección de envío seleccionada.
2. Verifica el carrito y el stock.
3. Crea una reserva de stock atómica.
4. Configura PayPal SDK con las credenciales del entorno.
5. Construye la lista de items con precios IVA incluido.
6. Crea el pago en PayPal y guarda el `payment_id` en la sesión.
7. Devuelve la URL de aprobación de PayPal.

## Firma

```python
def create_paypal_payment(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Cuerpo de la petición (JSON o form-data)

| Campo                  | Descripción                               |
|------------------------|-------------------------------------------|
| `shipping_address_id`  | ID de la dirección de envío seleccionada. |

## Respuesta exitosa

```json
{ "redirect": "https://www.paypal.com/checkoutnow?token=..." }
```

## Respuestas de error

| Código | Descripción                                        |
|--------|----------------------------------------------------|
| 400    | Carrito vacío, stock insuficiente, sin dirección, error de PayPal. |
| 405    | Método no permitido.                               |
| 500    | SDK de PayPal no instalado u otro error interno.   |

> [!NOTE]
> Requiere que `paypalrestsdk` esté instalado y las variables `PAYPAL_MODE`, `PAYPAL_CLIENT_ID` y `PAYPAL_CLIENT_SECRET` estén configuradas en `settings.py`.
