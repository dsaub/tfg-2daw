# `create_checkout_session`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/crear-sesion-pago/`  
**Tipo:** Vista privada (requiere autenticación)  
**Método HTTP:** Solo `POST`  
**Decoradores:** `@login_required`, `@csrf_exempt`

## Descripción

Crea una sesión de pago en Stripe Checkout y devuelve el ID de sesión al frontend. Es llamada por JavaScript para iniciar el flujo de pago con tarjeta.

El proceso es:

1. Obtiene y valida la dirección de envío seleccionada.
2. Verifica que el carrito no esté vacío y que no haya problemas de stock.
3. Crea una reserva de stock atómica para bloquear el inventario.
4. Construye los `line_items` con precios IVA incluido.
5. Crea la sesión en Stripe con URLs de retorno y cancelación.
6. Guarda el ID de sesión, la dirección y la reserva en la sesión HTTP.

## Firma

```python
def create_checkout_session(request: HttpRequest):
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
{ "sessionId": "cs_live_..." }
```

## Respuestas de error

| Código | Descripción                                      |
|--------|--------------------------------------------------|
| 400    | Carrito vacío, stock insuficiente, sin dirección. |
| 405    | Método no permitido.                              |
| 500    | Error interno al crear la sesión en Stripe.       |

> [!IMPORTANT]
> La reserva de stock creada expira en `STOCK_RESERVATION_MINUTES` minutos. Si el usuario no completa el pago en ese tiempo, el stock queda liberado automáticamente.
