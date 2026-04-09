# `portal_usuario`

**Archivo:** `tienda/views.py`  
**URL:** `/tienda/usuario/`  
**Tipo:** Vista privada (requiere autenticación)  
**Decorador:** `@login_required`

## Descripción

Dashboard del portal de usuario. Muestra un resumen de la actividad del usuario: total de pedidos, total de direcciones guardadas, pedidos recientes y mensajes recientes de vendedores no leídos.

## Firma

```python
def portal_usuario(request: HttpRequest):
```

## Parámetros

| Nombre    | Tipo          | Descripción           |
|-----------|---------------|-----------------------|
| `request` | `HttpRequest` | Petición HTTP de Django. |

## Contexto del template

| Variable          | Tipo      | Descripción                                                          |
|-------------------|-----------|----------------------------------------------------------------------|
| `total_orders`    | `int`     | Número total de pedidos realizados por el usuario.                   |
| `total_addresses` | `int`     | Número de direcciones de envío registradas.                          |
| `recent_orders`   | QuerySet  | Últimos 5 pedidos del usuario ordenados por fecha descendente.       |
| `recent_messages` | QuerySet  | Últimos 5 mensajes de vendedores no enviados por el propio usuario.  |

## Template

`tienda/portal_usuario.html`
