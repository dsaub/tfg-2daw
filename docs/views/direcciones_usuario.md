# `direcciones_usuario`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/direcciones/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Lista todas las direcciones de envío registradas por el usuario autenticado.

## Firma

```python
def direcciones_usuario(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable      | Tipo      | Descripción                              |
|---------------|-----------|------------------------------------------|
| `direcciones` | QuerySet  | Direcciones de envío del usuario.        |

## Template

`tienda/direcciones.html`
