# `send_test_email`

**Archivo:** `tienda/views.py`  
**URL:** No registrada en producción (uso interno de desarrollo)  
**Tipo:** Vista de utilidad / desarrollo

## Descripción

Vista de prueba que envía un correo de prueba a una dirección codificada en el código fuente. Devuelve un mensaje HTTP indicando si el correo se envió correctamente.

## Firma

```python
def send_test_email(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Retorno

`HttpResponse` con el texto `"Mira tu bandeja"` si el correo se envió, o el mensaje de error si falló.

> [!CAUTION]
> Esta vista es solo para desarrollo. La dirección de destino está codificada en el código fuente y no debe estar disponible en producción.
