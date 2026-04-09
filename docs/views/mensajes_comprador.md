# `mensajes_comprador`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/mensajes/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Muestra los mensajes enviados por los vendedores al comprador, agrupados por ítem de pedido. Permite al comprador ver el estado de sus pedidos y las comunicaciones de los vendedores.

## Firma

```python
def mensajes_comprador(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable      | Tipo      | Descripción                                                                 |
|---------------|-----------|-----------------------------------------------------------------------------|
| `order_items` | QuerySet  | `OrderItem` de pedidos del comprador, con mensajes, productos y vendedores precargados, ordenados por fecha descendente. |

## Template

`tienda/mensajes_comprador.html`
