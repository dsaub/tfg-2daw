# `_address_form_context`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Construye el diccionario de contexto que se pasa a los templates del formulario de dirección (`tienda/editar_direccion.html`). Centraliza los datos necesarios para renderizar el formulario, evitando repetición de código en las vistas de creación y edición de direcciones.

## Firma

```python
def _address_form_context(direccion=None) -> dict:
```

## Parámetros

| Nombre      | Tipo                        | Descripción                                                                   |
|-------------|-----------------------------|-------------------------------------------------------------------------------|
| `direccion` | `ShippingAddress` o `None`  | Instancia de dirección a editar, o `None` para un formulario en blanco. También acepta `request.POST` para repoblar el formulario tras un error de validación. |

## Retorno

Diccionario con las siguientes claves:

| Clave                     | Tipo   | Descripción                                      |
|---------------------------|--------|--------------------------------------------------|
| `direccion`               | objeto | La dirección pasada como argumento.              |
| `almeria_municipalities`  | lista  | Lista de municipios de Almería para el selector. |

## Uso interno

Utilizada en [`crear_direccion`](./crear_direccion.md) y [`editar_direccion`](./editar_direccion.md) para preparar el contexto del template.
