# `_normalize_location_text`

**Archivo:** `tienda/views.py`  
**Tipo:** Función auxiliar privada

## Descripción

Normaliza una cadena de texto que representa un nombre de localidad para facilitar comparaciones insensibles a mayúsculas, acentos y caracteres especiales.

El proceso de normalización aplica los siguientes pasos en orden:

1. Descompone el texto Unicode (NFD) para separar los caracteres base de sus diacríticos.
2. Elimina los diacríticos (tildes, diéresis, cedillas, etc.).
3. Elimina cualquier símbolo que no sea alfanumérico, espacio o guión.
4. Convierte guiones en espacios, pasa a minúsculas y colapsa espacios múltiples.

## Firma

```python
def _normalize_location_text(value: str) -> str:
```

## Parámetros

| Nombre  | Tipo  | Descripción                           |
|---------|-------|---------------------------------------|
| `value` | `str` | Texto de localidad a normalizar. Puede ser `None` o cadena vacía. |

## Retorno

Cadena de texto normalizada (minúsculas, sin acentos, sin símbolos especiales).

## Uso interno

Esta función es utilizada al construir el conjunto `ALMERIA_MUNICIPALITIES` al inicio del módulo, y también es llamada por [`_is_almeria_city`](./_is_almeria_city.md) para normalizar la ciudad antes de comprobar si pertenece a la provincia.

> [!NOTE]
> Al ser una función privada (prefijo `_`) no debe importarse ni llamarse desde fuera del módulo `views.py`.
