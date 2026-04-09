# `crear_direccion`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/direcciones/nueva/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Muestra el formulario para crear una nueva dirección de entrega y procesa su envío.

- **GET** → Renderiza el formulario vacío con la lista de municipios de Almería.
- **POST** → Valida y crea la dirección:
  - Comprueba que todos los campos obligatorios estén rellenos.
  - Valida que la ciudad pertenezca a la provincia de Almería.
  - Valida que el código postal sea de Almería (`04xxx`).
  - Guarda la dirección asociada al usuario con el país fijo `España`.

## Firma

```python
def crear_direccion(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Campos del formulario POST

| Campo             | Obligatorio | Descripción                                   |
|-------------------|-------------|-----------------------------------------------|
| `full_name`       | Sí          | Nombre completo del destinatario.             |
| `address_line_1`  | Sí          | Línea principal de la dirección.              |
| `address_line_2`  | No          | Línea secundaria (piso, puerta, etc.).        |
| `city`            | Sí          | Municipio (debe pertenecer a Almería).        |
| `postal_code`     | Sí          | Código postal (`04xxx`).                      |
| `phone`           | Sí          | Teléfono de contacto.                         |
| `is_default`      | No          | Marcar como dirección predeterminada (`on`).  |

## Redirecciones

| Caso   | Destino               |
|--------|-----------------------|
| Éxito  | `direcciones_usuario` |
| Error  | Mismo formulario      |

## Template

`tienda/editar_direccion.html`

> [!IMPORTANT]
> Solo se aceptan direcciones dentro de la provincia de Almería. El campo `country` siempre se fija a `España` y no es editable por el usuario.
