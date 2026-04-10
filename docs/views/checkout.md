# `checkout`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/checkout/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Renderiza la página de checkout con el resumen del carrito, las direcciones de envío del usuario y los posibles problemas de stock. Desde esta página el usuario puede iniciar el pago con Stripe o PayPal.

## Firma

```python
def checkout(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable              | Tipo            | Descripción                                                     |
|-----------------------|-----------------|-----------------------------------------------------------------|
| `cart`                | `Cart`          | Carrito actual del usuario.                                     |
| `cart_items`          | lista           | Ítems del carrito con productos precargados.                    |
| `addresses`           | QuerySet        | Direcciones de envío registradas por el usuario.               |
| `stock_issues`        | lista de `dict` | Conflictos de stock (vacía si no hay problemas).                |
| `reservation_minutes` | `int`           | Minutos de validez de la reserva de stock.                      |

## Template

`tienda/checkout.html`
