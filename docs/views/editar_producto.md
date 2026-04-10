# `editar_producto`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/venta/editar-producto/<id>/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Muestra el formulario de edición de un producto y procesa sus cambios. Solo el `creator` del producto puede editarlo; un intento de acceder a un producto ajeno lanza un error 404.

- **GET** → Renderiza el formulario con los datos actuales del producto.
- **POST** → Valida y aplica los cambios:
  - Campos obligatorios, precio (≥ 0) y stock (entero ≥ 0).
  - Si se sube una nueva imagen principal, se crea y sustituye la anterior.
  - Si se suben imágenes secundarias, se reemplazan todas las existentes.
  - Guarda el producto actualizado y redirige al panel de vendedor.

## Firma

```python
def editar_producto(request: HttpRequest, id: int):
```

## Parámetros

| Nombre    | Tipo          | Descripción                  |
|-----------|---------------|------------------------------|
| `request` | `HttpRequest` | Petición HTTP de Django.     |
| `id`      | `int`         | ID del producto a editar.    |

## Campos del formulario POST

Idénticos a [`crear_producto`](./crear_producto.md).

## Redirecciones

| Caso    | Destino         |
|---------|-----------------|
| Éxito   | `mis_productos` |
| Error   | Mismo formulario |

## Template

`tienda/editar_producto.html`

> [!NOTE]
> La caché Redis del producto (`product_{id}`) se invalida automáticamente al guardar el producto para que los cambios sean visibles de inmediato.
