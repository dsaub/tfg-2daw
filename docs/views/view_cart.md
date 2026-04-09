# `view_cart`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/carrito/`  
**Tipo:** Vista pública

## Descripción

Muestra el contenido actual del carrito de compra junto con los posibles problemas de stock. Excluye del cálculo de stock las reservas activas del propio usuario para no mostrar falsos avisos durante el checkout.

## Firma

```python
def view_cart(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable       | Tipo            | Descripción                                                    |
|----------------|-----------------|----------------------------------------------------------------|
| `cart`         | `Cart`          | Carrito actual del usuario.                                    |
| `cart_items`   | lista           | Ítems del carrito con sus productos relacionados precargados.  |
| `stock_issues` | lista de `dict` | Lista de conflictos de stock (vacía si no hay problemas).      |

## Template

`tienda/cart.html`
