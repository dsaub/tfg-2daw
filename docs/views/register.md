# `register`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/register/`  
**Tipo:** Vista pública

## Descripción

Gestiona el registro de nuevos usuarios.

- **GET** → Redirige al catálogo si el usuario ya está autenticado; de lo contrario muestra el formulario de registro.
- **POST** → Valida los datos e intenta crear la cuenta:
  - Comprueba que las contraseñas coincidan y tengan al menos 8 caracteres.
  - Comprueba que el email no esté ya registrado.
  - Genera un nombre de usuario único a partir del prefijo del email.
  - Crea el usuario y envía un correo de confirmación asíncrono (tarea Celery).
  - Redirige al catálogo con un mensaje de éxito.

## Firma

```python
def register(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Campos del formulario POST

| Campo              | Descripción                        |
|--------------------|------------------------------------|
| `name`             | Nombre del usuario.                |
| `email`            | Correo electrónico.                |
| `password`         | Contraseña (mínimo 8 caracteres).  |
| `password_confirm` | Confirmación de la contraseña.     |

## Redirecciones

| Caso                            | Destino  |
|---------------------------------|----------|
| Usuario ya autenticado          | `index`  |
| Registro exitoso                | `index`  |
| Error de validación             | Mismo template `tienda/register.html` |

## Template

`tienda/register.html`

> [!NOTE]
> El usuario se crea con `registration_status = "CR"` (pendiente de verificación). El acceso está bloqueado hasta que se verifique el correo electrónico.
