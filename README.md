# Comercialmería

Marketplace de comercio electrónico para la provincia de Almería. Proyecto final del ciclo de Desarrollo de Aplicaciones Web (2DAW).

## Características

- **Catálogo**: Productos con imágenes, categorías, búsqueda con autocompletado AJAX
- **Autenticación**: Registro con verificación por email, login con rate-limiting, recuperación de contraseña
- **Carrito**: Persistente para usuarios registrados y anónimos, con reserva de stock
- **Pagos**: Stripe (tarjeta) y PayPal, métodos de pago guardados
- **Panel vendedor**: CRUD de productos, gestión de pedidos, mensajería con compradores
- **Panel usuario**: Historial de compras, recibos PDF, direcciones, métodos de pago
- **Valoraciones**: Usuarios que han comprado pueden puntuar y reseñar productos
- **API REST**: Django Ninia (`/api/`)
- **Internacionalización**: Adaptado a España, solo provincia de Almería (04xxx)

## Tecnologías

| Categoría        | Tecnologías                                                                 |
|------------------|-----------------------------------------------------------------------------|
| Backend          | Python 3.14, Django 6.0                                                     |
| Base de datos    | PostgreSQL (producción), SQLite (desarrollo/tests)                          |
| Cache / Sesiones | Redis                                                                       |
| Tareas async     | Celery + Redis                                                              |
| Pagos            | Stripe, PayPal                                                              |
| Almacenamiento   | Local o S3 (AWS/R2)                                                         |
| PDF              | fpdf2                                                                       |
| API              | Django Ninia                                                                |
| Frontend         | Bootstrap 5, CSS personalizado, JavaScript nativo                           |
| Contenedor       | Docker (python:3.14-alpine)                                                 |
| CI/CD            | GitHub Actions                                                              |
| Proxy            | Nginx                                                                       |

## Requisitos

- **Redis**: `redis://127.0.0.1:6379/1`
- **PostgreSQL** (opcional, si `POSTGRES_ENABLED=False` usa SQLite)
- Copiar `.env.example` a `.env` y configurar

## Inicio rápido

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

La aplicación estará en `http://localhost:8000/tienda/`.

## Comandos

```bash
make test          # Ejecutar tests
python manage.py runserver            # Servidor desarrollo
python manage.py migrate              # Migraciones
python manage.py collectstatic        # Archivos estáticos (producción)
```

## Estructura

```
proyecto/              # Configuración Django
tienda/                # Aplicación principal
  ├── models.py        # 15 modelos
  ├── views.py         # ~80 vistas
  ├── urls.py          # 76 rutas
  ├── api.py           # API REST
  ├── tasks.py         # Tareas Celery
  ├── forms.py         # Formularios
  ├── admin.py         # Panel de administración
  ├── pdf.py           # Generación de recibos
  ├── tests.py         # Tests (2089 líneas)
  ├── templatetags/    # Filtros de plantilla
  ├── templates/       # 38 plantillas
  └── static/          # CSS, JS, imágenes
docs/                  # Documentación
```

## Despliegue

```bash
git push origin       # GitHub
git push github       # GitHub (alias)
```

GitHub Actions construye y publica la imagen Docker en `ghcr.io/dsaub/proyecto-mvc:development`.

## Licencia

Proyecto educativo sin licencia específica.
