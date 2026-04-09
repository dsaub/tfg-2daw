# `stripe_config`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/stripe-config/`  
**Tipo:** Vista pública (CSRF exento)  
**Método HTTP:** `GET`  
**Decorador:** `@csrf_exempt`

## Descripción

Endpoint de configuración de Stripe que expone la clave pública (`publishable key`) al frontend JavaScript. Es llamado por el cliente antes de iniciar una sesión de Stripe Checkout para obtener la clave necesaria para inicializar `stripe.js`.

## Firma

```python
def stripe_config(request):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Respuesta

```json
{
  "publicKey": "pk_live_..."
}
```

> [!CAUTION]
> Esta vista está marcada con `@csrf_exempt`. Asegúrate de que solo expone la clave **pública** de Stripe, nunca la clave secreta.
