# `_get_reservation_owner_filters`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Construye el diccionario de filtros para identificar al propietario de una reserva de stock, adaptándose según si el usuario está autenticado o no.

- Usuario autenticado → filtra por `user`.
- Usuario anónimo → filtra por `session_key`.

## Firma

```python
def _get_reservation_owner_filters(request: HttpRequest) -> dict:
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Retorno

Diccionario listo para usar como `**kwargs` en consultas ORM de `StockReservation`.

## Uso interno

Llamada desde [`_create_stock_reservation_for_cart`](./_create_stock_reservation_for_cart.md), [`_cancel_active_stock_reservations_for_request`](./_cancel_active_stock_reservations_for_request.md), [`_get_session_stock_reservation`](./_get_session_stock_reservation.md) y [`_get_active_reservation_ids_for_request`](./_get_active_reservation_ids_for_request.md).
