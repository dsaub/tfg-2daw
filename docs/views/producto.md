# `producto`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/producto/<id>/`  
**Tipo:** Vista pública

## Descripción

Muestra la página de detalle de un producto. Implementa una capa de caché en Redis para mejorar el rendimiento: el producto se almacena durante 5 minutos con la clave `product_{id}`. Si el producto no está en caché, se obtiene de la base de datos junto con sus relaciones (`category`, `primary_image`, `creator`, `secondary_images`) y se guarda en caché.

## Firma

```python
def producto(request: HttpRequest, id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción                    |
|-----------|---------------|--------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.       |
| `id`      | `int`         | Identificador del producto.    |

## Contexto del template

| Variable  | Tipo      | Descripción           |
|-----------|-----------|-----------------------|
| `product` | `Product` | Instancia del producto. |

## Template

`tienda/producto.html`

> [!TIP]
> La caché se invalida automáticamente cuando el producto es editado o eliminado (ver [`editar_producto`](./editar_producto.md) y [`borrar_producto`](./borrar_producto.md)). La clave de caché tiene el formato `:1:product_{id}` en Redis (prefijo de la base de datos 1).
