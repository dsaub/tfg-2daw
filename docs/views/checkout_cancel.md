# `checkout_cancel`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/pago-cancelado/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Página que se muestra cuando el usuario cancela el proceso de pago en Stripe o PayPal. Cancela las reservas de stock activas y limpia los datos de reserva de la sesión, devolviendo el inventario bloqueado.

## Firma

```python
def checkout_cancel(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Template

`tienda/checkout_cancel.html`
