# `cambiar_estado_pedido`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/venta/pedidos/estado/<item_id>/`  
**Tipo:** Vista privada (requiere autenticación)  
**Método HTTP:** Solo `POST`  
**Decorador:** `@login_required`

## Descripción

Permite al vendedor cambiar el estado de un ítem de pedido que le pertenece. Solo acepta peticiones POST; cualquier otro método devuelve un error.

Valida que el nuevo estado sea uno de los valores definidos en `OrderItem.STATUS_CHOICES`.

## Firma

```python
def cambiar_estado_pedido(request: HttpRequest, item_id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |
| `item_id` | `int`         | ID del `OrderItem` a actualizar. |

## Parámetros POST

| Campo    | Descripción                                    |
|----------|------------------------------------------------|
| `estado` | Nuevo estado del pedido (valor de `STATUS_CHOICES`). |

## Redirecciones

Siempre redirige a `pedidos_vendedor`.
