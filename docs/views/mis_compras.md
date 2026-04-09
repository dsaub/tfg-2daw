# `mis_compras`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/mis-compras/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Muestra el historial completo de pedidos realizados por el usuario autenticado, ordenados de más reciente a más antiguo.

## Firma

```python
def mis_compras(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable       | Tipo      | Descripción                                     |
|----------------|-----------|-------------------------------------------------|
| `orders`       | QuerySet  | Todos los pedidos del usuario con sus ítems precargados. |
| `total_orders` | `int`     | Número total de pedidos.                        |

## Template

`tienda/mis_compras.html`
