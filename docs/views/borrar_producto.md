# `borrar_producto`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/venta/borrar-producto/<id>/`  
**Tipo:** Vista privada (requiere autenticación)  
**Método HTTP:** Solo `POST`  
**Decorador:** `@login_required`

## Descripción

Elimina un producto del vendedor autenticado. Solo acepta peticiones POST. Verifica que el producto pertenezca al usuario actual; de lo contrario lanza un error 404.

## Firma

```python
def borrar_producto(request: HttpRequest, id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción                  |
|-----------|---------------|------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.     |
| `id`      | `int`         | ID del producto a eliminar.  |

## Redirecciones

Siempre redirige a `mis_productos`.

> [!CAUTION]
> La eliminación es permanente. El producto y sus imágenes asociadas se borran de la base de datos. Asegúrate de que no haya pedidos activos vinculados al producto antes de eliminarlo.
