# `logout`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/logout/`  
**Tipo:** Vista pública

## Descripción

Cierra la sesión del usuario autenticado actual. Registra el evento de cierre de sesión en el logger de auditoría y redirige al catálogo con un mensaje de confirmación.

## Firma

```python
def logout(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Redirecciones

Siempre redirige a `index` tras el cierre de sesión.

> [!NOTE]
> El evento se registra con `user_id`, `email` e IP del cliente en el logger `tienda.audit`, independientemente de si había un usuario autenticado o no.
