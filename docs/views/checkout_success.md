# `checkout_success`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/pago-exitoso/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Página de confirmación tras un pago exitoso con Stripe. Crea el pedido a partir del carrito usando la sesión Stripe y la reserva de stock almacenadas en la sesión HTTP.

Si la creación del pedido falla (por ejemplo, porque la reserva caducó), muestra un error y redirige al checkout.

Tras confirmar el pedido, limpia las claves de sesión relacionadas con el pago.

## Firma

```python
def checkout_success(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable | Tipo    | Descripción              |
|----------|---------|--------------------------|
| `order`  | `Order` | Pedido recién creado.    |

## Template

`tienda/checkout_success.html`

## Redirecciones

| Caso              | Destino    |
|-------------------|------------|
| Error en el pedido | `checkout` |
