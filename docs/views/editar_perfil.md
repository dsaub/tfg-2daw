# `editar_perfil`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/editar-perfil/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Permite al usuario editar su información de perfil (nombre, apellido y correo electrónico).

- **GET** → Renderiza el formulario con los datos actuales.
- **POST** → Valida y guarda los cambios.
  - Verifica que el nuevo email no esté ya en uso por otro usuario.
  - Actualiza `first_name`, `last_name` y `email` del usuario.
  - Redirige al portal de usuario.

## Firma

```python
def editar_perfil(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Campos del formulario POST

| Campo        | Descripción             |
|--------------|-------------------------|
| `first_name` | Nombre del usuario.     |
| `last_name`  | Apellido del usuario.   |
| `email`      | Correo electrónico.     |

## Redirecciones

| Caso   | Destino          |
|--------|------------------|
| Éxito  | `portal_usuario` |
| Error  | Mismo template   |

## Template

`tienda/editar_perfil.html`
