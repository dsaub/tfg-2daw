# `get_or_create_cart`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar pública

## Descripción

Obtiene o crea el carrito de compra asociado a la sesión o al usuario actual.

- Si el usuario está autenticado, el carrito se asocia a su instancia `User`.
- Si el usuario es anónimo, se utiliza la clave de sesión (`session_key`). Si la sesión no tiene clave, se crea automáticamente.

## Firma

```python
def get_or_create_cart(request) -> Cart:
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Retorno

Instancia de `Cart` existente o recién creada.

## Uso

Es la función de entrada estándar para acceder al carrito desde cualquier vista. Llamada en [`add_to_cart`](./add_to_cart.md), [`view_cart`](./view_cart.md), [`update_cart_item`](./update_cart_item.md), [`remove_from_cart`](./remove_from_cart.md), [`clear_cart`](./clear_cart.md), [`create_order_from_cart`](./create_order_from_cart.md), [`checkout`](./checkout.md) y las vistas de pago.
