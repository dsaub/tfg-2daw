# `search_suggestions`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/sugerencias/`  
**Tipo:** Vista pública (API AJAX)

## Descripción

Endpoint JSON que devuelve hasta 8 sugerencias de productos para el autocompletado de la barra de búsqueda. Solo responde si el término de búsqueda tiene al menos 2 caracteres.

Busca coincidencias en el nombre del producto y en la descripción breve.

## Firma

```python
def search_suggestions(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Parámetros GET

| Parámetro | Tipo  | Descripción                              |
|-----------|-------|------------------------------------------|
| `q`       | `str` | Texto a buscar (mínimo 2 caracteres).    |

## Respuesta

```json
{
  "suggestions": [
    { "name": "Camiseta azul", "id": 42, "price": 19.99 }
  ]
}
```

Si la consulta tiene menos de 2 caracteres, `suggestions` es una lista vacía.
