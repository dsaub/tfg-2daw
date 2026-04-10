# `crear_producto`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/venta/crear-producto/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Muestra el formulario para crear un nuevo producto y procesa su envío.

- **GET** → Renderiza el formulario vacío con las categorías disponibles.
- **POST** → Valida los datos, crea el producto y sus imágenes asociadas:
  - Valida campos obligatorios, precio (≥ 0) y stock (entero ≥ 0).
  - Crea la imagen principal si se proporciona.
  - Crea el producto asociado al usuario autenticado como `creator`.
  - Agrega imágenes secundarias si se proporcionan.
  - Redirige al panel de vendedor con un mensaje de éxito.

## Firma

```python
def crear_producto(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Campos del formulario POST

| Campo               | Tipo     | Obligatorio | Descripción                            |
|---------------------|----------|-------------|----------------------------------------|
| `name`              | texto    | Sí          | Nombre del producto.                   |
| `briefdesc`         | texto    | No          | Descripción breve.                     |
| `description`       | texto    | Sí          | Descripción completa.                  |
| `price`             | decimal  | Sí          | Precio base sin IVA (≥ 0).             |
| `stock`             | entero   | Sí          | Unidades disponibles (≥ 0).            |
| `category`          | `int`    | Sí          | ID de la categoría.                    |
| `primary_image`     | archivo  | No          | Imagen principal del producto.         |
| `secondary_images`  | archivos | No          | Imágenes secundarias (lista).          |

## Redirecciones

| Caso          | Destino         |
|---------------|-----------------|
| Éxito         | `mis_productos` |
| Error         | Mismo formulario |

## Template

`tienda/crear_producto.html`
