# `login`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/login/`  
**Tipo:** Vista pública

## Descripción

Gestiona el inicio de sesión de un usuario.

- **GET** → Renderiza el formulario de login.
- **POST** → Autentica al usuario con email y contraseña.
  - Si el correo no existe: muestra error y registra el intento fallido.
  - Si la cuenta no está verificada (`registration_status == "CR"`): muestra error sin autenticar.
  - Si las credenciales son correctas: inicia la sesión, configura su duración, envía un correo de bienvenida asíncrono (tarea Celery) y redirige al catálogo.
  - Si la contraseña es incorrecta: muestra error y registra el intento fallido.

## Firma

```python
def login(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Campos del formulario POST

| Campo       | Descripción                                                           |
|-------------|-----------------------------------------------------------------------|
| `email`     | Correo electrónico del usuario.                                       |
| `password`  | Contraseña del usuario.                                               |
| `remember`  | Si está presente, la sesión dura 14 días; de lo contrario, expira al cerrar el navegador. |

## Redirecciones

| Caso                        | Destino         |
|-----------------------------|-----------------|
| Login correcto              | `index`         |
| Login fallido / cuenta no verificada | Mismo template `tienda/login.html` |

## Template

`tienda/login.html`

> [!NOTE]
> Los intentos de inicio de sesión (correctos y fallidos) se registran en el logger de auditoría `tienda.audit` con la IP del cliente.
