# `_get_client_ip`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Obtiene la dirección IP real del cliente a partir de la petición HTTP.

Cuando la aplicación se encuentra detrás de un proxy inverso (como Nginx), la IP real del cliente viaja en la cabecera `X-Forwarded-For`. Esta función la extrae y devuelve la primera IP de la cadena. Si dicha cabecera no está presente, devuelve el valor de `REMOTE_ADDR`.

## Firma

```python
def _get_client_ip(request: HttpRequest) -> str:
```

## Parámetros

| Nombre    | Tipo          | Descripción        |
|-----------|---------------|--------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Retorno

Cadena de texto con la dirección IP del cliente. Devuelve una cadena vacía si no hay ninguna disponible.

## Uso interno

Llamada desde [`login`](./login.md), [`register`](./register.md) y [`logout`](./logout.md) para incluir la IP del cliente en los registros de auditoría.

> [!CAUTION]
> La cabecera `X-Forwarded-For` puede ser falsificada por un cliente malicioso. Confiar en ella para control de acceso o límites de tasa sin validación adicional conlleva riesgos de seguridad.
