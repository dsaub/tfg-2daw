# `_is_almeria_postal_code`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Valida que un código postal pertenezca a la provincia de Almería.

Un código postal de Almería tiene exactamente 5 dígitos y comienza con el prefijo `04` (definido en `tienda/vars.py` como `ALMERIA_POSTAL_CODE_PREFIX`).

## Firma

```python
def _is_almeria_postal_code(postal_code: str) -> bool:
```

## Parámetros

| Nombre        | Tipo  | Descripción                            |
|---------------|-------|----------------------------------------|
| `postal_code` | `str` | Código postal a validar. Se elimina el espacio inicial/final antes de la comprobación. |

## Retorno

`True` si el código postal es válido para Almería, `False` en caso contrario.

## Uso interno

Llamada desde [`crear_direccion`](./crear_direccion.md) y [`editar_direccion`](./editar_direccion.md) para rechazar direcciones de envío fuera de la provincia.

> [!IMPORTANT]
> Solo se aceptan envíos dentro de la provincia de Almería. Cualquier código postal que no comience por `04` será rechazado.
