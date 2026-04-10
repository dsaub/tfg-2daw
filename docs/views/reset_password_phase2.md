# `reset_password_phase2`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/reset-password/<code>/`  
**Tipo:** Vista pública

## Descripción

Segunda fase del flujo de restablecimiento de contraseña. El usuario llega aquí desde el enlace enviado a su correo electrónico.

- **GET** → Renderiza el formulario para introducir la nueva contraseña.
- **POST** → Valida las contraseñas, actualiza la contraseña del usuario y redirige al catálogo.
- Cualquier otro método → lanza `Http404`.

Si el código no existe o no corresponde al modo `RESET_PASSWORD`, lanza `Http404`.

## Firma

```python
def reset_password_phase2(request: HttpRequest, code: str):
```

## Parámetros

| Nombre    | Tipo          | Descripción                             |
|-----------|---------------|-----------------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.                |
| `code`    | `str`         | Código de verificación del email de recuperación. |

## Campos del formulario POST

| Campo             | Descripción                              |
|-------------------|------------------------------------------|
| `password`        | Nueva contraseña.                        |
| `verify_password` | Confirmación de la nueva contraseña.     |

## Contexto del template

| Variable | Tipo  | Descripción                               |
|----------|-------|-------------------------------------------|
| `code`   | `str` | Código necesario para el envío del formulario. |

## Redirecciones

| Caso                         | Destino / Respuesta        |
|------------------------------|----------------------------|
| Contraseñas no coinciden     | Mismo formulario con error |
| Cambio exitoso               | `index`                    |
| Código inválido o modo incorrecto | `Http404`             |

## Template

`tienda/reset_password_phase2.html`
