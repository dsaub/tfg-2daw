# Redis Setup - Configuración de Redis para Sesiones

## Configuración Implementada

Este proyecto utiliza Redis para almacenar las sesiones de usuario, mejorando el rendimiento y la escalabilidad.

### Paquetes Instalados
- **django-redis 5.4.0**: Backend de caché Redis para Django
- **redis 5.2.1**: Cliente Python para Redis

### Configuración en settings.py

```python
# Redis Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session Configuration - Use Redis for session storage
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### Uso en el Proyecto

El proyecto utiliza Redis para:

1. **Sesiones de usuario**: Todas las sesiones se almacenan en Redis (base de datos 1)
2. **Cacheo de productos**: Los productos visitados se cachean por 5 minutos
   - Primera visita: Se carga desde la base de datos y se cachea
   - Siguientes visitas: Se sirve desde caché (mucho más rápido)
   - Después de 5 minutos: Se recarga desde la BD y se vuelve a cachear
   - Al editar/borrar un producto: Se invalida automáticamente su caché

## Instalación de Redis

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Linux (Arch Linux)
```bash
sudo pacman -S redis
sudo systemctl start valkey
sudo systemctl enable valkey
# En Arch, Redis se llama Valkey (fork de Redis)
# Comando CLI: valkey-cli en lugar de redis-cli
```

### macOS
```bash
brew install redis
brew services start redis
```

### Windows
Descargar desde: https://github.com/microsoftarchive/redis/releases

## Verificar que Redis está Funcionando

```bash
# Verificar estado del servicio
sudo systemctl status redis-server

# Conectarse a Redis CLI
redis-cli

# En Redis CLI, probar conexión:
ping
# Debería responder: PONG

# Ver todas las claves almacenadas
keys *

# Salir de Redis CLI
exit
```

## Probar la Configuración

```bash
# Conectarse a Redis y ver sesiones y productos cacheados
valkey-cli    # o redis-cli según tu sistema
SELECT 1      # Usa la base de datos 1 (definida en LOCATION)
KEYS *        # Ver todas las claves almacenadas

# Ver productos cacheados
KEYS *product*

# Ver sesiones
KEYS *session*

# Ver el contenido de una clave específica
GET <key_name>

# Ver el TTL (tiempo restante) de una clave
TTL <key_name>
```

### Ejemplo de Claves en Redis

- Productos: `:1:product_<id>` (ej: `:1:product_7`)
- Sesiones: `:1:django.contrib.sessions.cache<session_id>`
- Cache general: `:1:test_key`

## Configuración de Producción

Para producción, considera:

1. **Configurar contraseña en Redis**:
```bash
# En /etc/redis/redis.conf
requirepass tu_contraseña_segura
```

2. **Actualizar settings.py**:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://:tu_contraseña_segura@127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

3. **Persistencia de datos**: Redis guarda snapshots automáticamente, pero puedes configurar:
```bash
# En /etc/redis/redis.conf
save 900 1      # Guardar cada 15 min si hay al menos 1 cambio
save 300 10     # Guardar cada 5 min si hay al menos 10 cambios
save 60 10000   # Guardar cada 1 min si hay al menos 10000 cambios
```

## Ventajas de Redis para Sesiones

1. **Rendimiento**: Redis es extremadamente rápido (en memoria)
2. **Escalabilidad**: Permite múltiples servidores compartiendo sesiones
3. **Expiración automática**: Las sesiones expiran automáticamente
4. **Persistencia**: Opcionalmente puede persistir datos en disco

## Ventajas del Cacheo de Productos

1. **Velocidad**: ~15x más rápido cargar desde caché vs base de datos
2. **Reducción de carga**: Menos queries a la base de datos
3. **Mejor UX**: Páginas de producto cargan instantáneamente
4. **Auto-invalidación**: El caché se limpia automáticamente al editar/borrar productos

### Flujo de Cacheo de Productos

```
Usuario visita producto
        ↓
¿Está en caché? → NO → Cargar de BD → Cachear por 5 min → Mostrar
        ↓
       SÍ
        ↓
¿Pasaron 5 min? → SÍ → Cargar de BD → Cachear por 5 min → Mostrar
        ↓
       NO
        ↓
    Servir desde caché → Mostrar
```

## Monitoreo

```bash
# Ver estadísticas en tiempo real
redis-cli --stat

# Monitor de comandos en tiempo real
redis-cli monitor

# Ver información del servidor
redis-cli INFO
```

## Limpieza de Sesiones

Las sesiones en Redis expiran automáticamente según `SESSION_COOKIE_AGE` de Django (por defecto 2 semanas).

Para limpiar manualmente todas las sesiones:
```bash
redis-cli
SELECT 1
FLUSHDB
```

## Troubleshooting

### Error: "Connection refused"
- Verificar que Redis está corriendo: `sudo systemctl status redis-server`
- Iniciar Redis: `sudo systemctl start redis-server`

### Sesiones no se guardan
- Verificar conexión a Redis: `redis-cli ping`
- Revisar logs: `sudo journalctl -u redis-server -n 50`

### Alto uso de memoria
- Ver uso de memoria: `redis-cli INFO memory`
- Configurar límite: En redis.conf agregar `maxmemory 256mb`
- Política de desalojo: `maxmemory-policy allkeys-lru`
