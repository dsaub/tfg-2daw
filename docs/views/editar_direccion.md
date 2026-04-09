# `editar_direccion`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/direcciones/editar/<id>/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Muestra el formulario para editar una dirección de entrega existente y procesa sus cambios. Solo el propietario de la dirección puede editarla; intentar acceder a una dirección ajena lanza un error 404.

Aplica las mismas validaciones de zona de envío que [`crear_direccion`](./crear_direccion.md).

## Firma

```python
def editar_direccion(request: HttpRequest, id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción                      |
|-----------|---------------|----------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.         |
| `id`      | `int`         | ID de la dirección a editar.     |

## Campos del formulario POST

Idénticos a [`crear_direccion`](./crear_direccion.md).

## Redirecciones

| Caso   | Destino               |
|--------|-----------------------|
| Éxito  | `direcciones_usuario` |
| Error  | Mismo formulario      |

## Template

`tienda/editar_direccion.html`
