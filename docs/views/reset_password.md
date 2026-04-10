# `reset_password`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/reset-password/`  
**Tipo:** Vista pública

## Descripción

Gestiona la solicitud de restablecimiento de contraseña.

- **GET** → Renderiza el formulario para introducir el correo electrónico. Si el usuario ya está autenticado, redirige al catálogo.
- **POST** → Lanza la tarea Celery `enviar_correo_recuperacion` para enviar un correo con el enlace de recuperación si existe una cuenta con ese email. Siempre muestra el mismo mensaje informativo para no revelar si el email existe.

> [!NOTE]
> En el código fuente hay dos definiciones de `reset_password`. La segunda (línea 1636) sobreescribe a la primera (línea 1626). Solo la segunda definición está activa en tiempo de ejecución.

## Firma

```python
def reset_password(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Campos del formulario POST

| Campo   | Descripción                             |
|---------|-----------------------------------------|
| `email` | Correo electrónico de la cuenta.        |

## Template

`tienda/reset_password.html`

> [!TIP]
> Para evitar la enumeración de usuarios, el mensaje de respuesta siempre es el mismo independientemente de si el email existe o no.
