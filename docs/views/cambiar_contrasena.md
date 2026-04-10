# `cambiar_contrasena`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/cambiar-contrasena/`  
**Tipo:** Vista privada (requiere autenticación)  
**Método HTTP:** Solo `POST`  
**Decorador:** `@login_required`

## Descripción

Cambia la contraseña del usuario autenticado tras verificar la contraseña actual.

- Verifica que la contraseña actual sea correcta.
- Comprueba que la nueva contraseña y su confirmación coincidan.
- Valida que la nueva contraseña tenga al menos 8 caracteres.
- Establece la nueva contraseña y vuelve a iniciar sesión para mantener la sesión activa.

## Firma

```python
def cambiar_contrasena(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Campos del formulario POST

| Campo              | Descripción                          |
|--------------------|--------------------------------------|
| `current_password` | Contraseña actual del usuario.       |
| `new_password`     | Nueva contraseña (mínimo 8 caracteres). |
| `confirm_password` | Confirmación de la nueva contraseña. |

## Redirecciones

| Caso   | Destino          |
|--------|------------------|
| Éxito  | `portal_usuario` |
| Error  | Template `tienda/editar_perfil.html` |
| GET    | `editar_perfil`  |

> [!NOTE]
> Tras cambiar la contraseña se llama a `auth_login` para re-autenticar al usuario y evitar que la sesión quede invalidada.
