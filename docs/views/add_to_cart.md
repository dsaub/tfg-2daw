# `add_to_cart`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/carrito/agregar/<product_id>/`  
**Tipo:** Vista pública

## Descripción

Agrega un producto al carrito del usuario (autenticado o anónimo). Antes de añadir, cancela cualquier reserva de stock activa para que el inventario se recalcule limpiamente.

- Si el producto ya existe en el carrito, incrementa la cantidad.
- Valida que la cantidad resultante no supere el stock disponible.
- Si la petición incluye la cabecera `X-Requested-With: XMLHttpRequest`, devuelve una respuesta JSON en lugar de redirigir.

## Firma

```python
def add_to_cart(request: HttpRequest, product_id: int):
```

## Parámetros

| Nombre       | Tipo          | Descripción                      |
|--------------|---------------|----------------------------------|
| `request`    | `HttpRequest` | Petición HTTP de Django.         |
| `product_id` | `int`         | ID del producto a agregar.       |

## Parámetros POST

| Campo      | Tipo  | Por defecto | Descripción              |
|------------|-------|-------------|--------------------------|
| `quantity` | `int` | `1`         | Cantidad a agregar.      |

## Redirecciones

| Caso                            | Destino                  |
|---------------------------------|--------------------------|
| Éxito (no AJAX)                 | `view_cart`              |
| Stock insuficiente / cantidad inválida | `producto` (detalle del producto) |
| Producto no encontrado          | `index`                  |

## Respuesta AJAX

```json
{
  "success": true,
  "cart_count": 3,
  "message": "..."
}
```
