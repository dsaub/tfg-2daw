# `paypal_execute`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/paypal/ejecutar/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Procesa la confirmación de un pago de PayPal después de que el usuario lo aprueba en el portal de PayPal. PayPal redirige al usuario a esta URL con los parámetros `PayerID` y el `token` de la transacción.

El proceso es:

1. Obtiene `payment_id` de la sesión y `PayerID` de los parámetros GET.
2. Configura y ejecuta el pago en PayPal.
3. Si el pago es exitoso, llama a [`create_order_from_cart`](./create_order_from_cart.md) para crear el pedido.
4. Limpia las claves de sesión relacionadas con el pago.
5. Renderiza la página de éxito con el pedido.

## Firma

```python
def paypal_execute(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Parámetros GET (de PayPal)

| Parámetro  | Descripción                                  |
|------------|----------------------------------------------|
| `PayerID`  | ID del pagador proporcionado por PayPal.     |

## Template (en caso de éxito)

`tienda/checkout_success.html`

## Redirecciones

| Caso              | Destino    |
|-------------------|------------|
| Datos incompletos / error en el pedido | `checkout` |
