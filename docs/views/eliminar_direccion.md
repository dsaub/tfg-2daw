# `eliminar_direccion`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/direcciones/eliminar/<id>/`  
**Tipo:** Vista privada (requiere autenticación)  
**Método HTTP:** Solo `POST`  
**Decorador:** `@login_required`

## Descripción

Elimina una dirección de entrega del usuario. Solo acepta peticiones POST. Verifica que la dirección pertenezca al usuario actual; de lo contrario lanza un error 404.

## Firma

```python
def eliminar_direccion(request: HttpRequest, id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción                       |
|-----------|---------------|-----------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.          |
| `id`      | `int`         | ID de la dirección a eliminar.    |

## Redirecciones

Siempre redirige a `direcciones_usuario`.
