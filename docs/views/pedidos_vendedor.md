# `pedidos_vendedor`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/venta/pedidos/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Muestra todos los pedidos en los que el usuario autenticado figura como vendedor (es decir, `OrderItem` donde `seller` es el usuario). Incluye la información del comprador, la dirección de envío y los mensajes de cada pedido.

## Firma

```python
def pedidos_vendedor(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable       | Tipo      | Descripción                                             |
|----------------|-----------|---------------------------------------------------------|
| `pedidos`      | QuerySet  | `OrderItem` del vendedor ordenados por fecha descendente, con relaciones precargadas. |
| `total_pedidos`| `int`     | Número total de pedidos del vendedor.                   |

## Template

`tienda/pedidos_vendedor.html`
