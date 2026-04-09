# `_get_or_create_session_key`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Garantiza que la sesión HTTP tiene una clave (`session_key`) activa. Si la sesión aún no tiene clave asignada, la crea explícitamente. Devuelve la clave de sesión resultante.

## Firma

```python
def _get_or_create_session_key(request: HttpRequest) -> str:
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Retorno

Cadena con la clave de sesión activa.

## Uso interno

Utilizada en [`_get_reservation_owner_filters`](./_get_reservation_owner_filters.md) y [`_create_stock_reservation_for_cart`](./_create_stock_reservation_for_cart.md) para identificar al usuario anónimo en las reservas de stock.
