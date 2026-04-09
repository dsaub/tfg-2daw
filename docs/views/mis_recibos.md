# `mis_recibos`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/mis-recibos/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Muestra los recibos del usuario, es decir, los pedidos con estado `PAID`. Útil para consultar el historial de pagos completados.

## Firma

```python
def mis_recibos(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable         | Tipo      | Descripción                                         |
|------------------|-----------|-----------------------------------------------------|
| `receipts`       | QuerySet  | Pedidos pagados del usuario, con ítems precargados. |
| `total_receipts` | `int`     | Número total de recibos.                            |

## Template

`tienda/mis_recibos.html`
