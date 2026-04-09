# `_get_active_reservation_ids_for_request`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Devuelve los IDs de todas las reservas de stock activas y no caducadas que pertenecen al usuario o sesión actuales. Antes de la consulta, libera automáticamente las reservas expiradas.

## Firma

```python
def _get_active_reservation_ids_for_request(request: HttpRequest) -> list[int]:
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Retorno

Lista de enteros con los IDs de reservas activas. Puede estar vacía.

## Uso interno

Llamada desde [`view_cart`](./view_cart.md) y [`checkout`](./checkout.md) para excluir la propia reserva del usuario al calcular el stock disponible, evitando así falsos avisos de stock insuficiente durante el proceso de pago.
