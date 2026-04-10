# `verify`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/verificar/<code>/`  
**Tipo:** Vista pública

## Descripción

Verifica la cuenta de un usuario a partir de un código de verificación enviado por correo electrónico. Cuando el código es válido y corresponde al modo `VERIFY_ACCOUNT`, actualiza el estado de registro del usuario a `ACTIVE` y elimina el código usado.

## Firma

```python
def verify(request: HttpRequest, code: str):
```

## Parámetros

| Nombre    | Tipo          | Descripción                             |
|-----------|---------------|-----------------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.                |
| `code`    | `str`         | Código de verificación único del email. |

## Redirecciones

| Caso                        | Destino / Respuesta                                         |
|-----------------------------|-------------------------------------------------------------|
| Verificación exitosa        | `index`                                                     |
| Código no encontrado        | `HttpResponse` con mensaje de error HTML                    |

> [!NOTE]
> El código de verificación se elimina de la base de datos tras ser utilizado, por lo que no puede usarse dos veces.
