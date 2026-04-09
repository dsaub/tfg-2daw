# `enviar_mensaje_pedido`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/venta/pedidos/mensaje/<item_id>/`  
**Tipo:** Vista privada (requiere autenticación)  
**Método HTTP:** Solo `POST`  
**Decorador:** `@login_required`

## Descripción

Permite al vendedor enviar un mensaje al comprador sobre un ítem de pedido específico. El mensaje se almacena como un registro `OrderMessage` vinculado al `OrderItem` y al remitente.

Rechaza mensajes vacíos y cualquier método que no sea POST.

## Firma

```python
def enviar_mensaje_pedido(request: HttpRequest, item_id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |
| `item_id` | `int`         | ID del `OrderItem` al que va dirigido el mensaje. |

## Parámetros POST

| Campo     | Descripción                    |
|-----------|--------------------------------|
| `mensaje` | Texto del mensaje (requerido). |

## Redirecciones

Siempre redirige a `pedidos_vendedor`.
