# `_is_almeria_city`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Comprueba si el nombre de un municipio o localidad pertenece a la provincia de Almería.

La comprobación se realiza normalizando el texto de entrada con [`_normalize_location_text`](./_normalize_location_text.md) y verificando si el resultado está presente en el conjunto `ALMERIA_MUNICIPALITIES`, que se construye a partir de `ALMERIA_MUNICIPALITIES_DISPLAY` definido en `tienda/vars.py`.

## Firma

```python
def _is_almeria_city(city: str) -> bool:
```

## Parámetros

| Nombre | Tipo  | Descripción                                  |
|--------|-------|----------------------------------------------|
| `city` | `str` | Nombre del municipio o localidad a comprobar. |

## Retorno

`True` si la ciudad pertenece a Almería, `False` en caso contrario.

## Uso interno

Llamada desde [`crear_direccion`](./crear_direccion.md) y [`editar_direccion`](./editar_direccion.md) para validar que la dirección de envío esté dentro de la zona de cobertura.

> [!NOTE]
> El conjunto `ALMERIA_MUNICIPALITIES` incluye variantes sin el artículo inicial (`la`, `los`) para mayor flexibilidad en la comparación.
