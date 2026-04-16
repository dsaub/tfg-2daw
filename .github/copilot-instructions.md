# Copilot Instructions - Django Tienda Project

## Project Overview
This is a Django 6.0.1 e-commerce application ("tienda" = store) with a monolithic architecture. The project uses SQLite for development and Bootstrap 5.0.2 for styling.

## Architecture
- **Main project**: `proyecto/` - Django settings, root URL configuration, WSGI/ASGI config
- **Tienda app**: `tienda/` - Core e-commerce functionality (currently minimal, ready for expansion)
- **Database**: SQLite (`db.sqlite3`) for local development
- **Static files**: Bootstrap 5.0.2 bundled in `tienda/static/css/styles.css` (9929 lines), images in `tienda/static/img/`

## URL Routing Pattern
URLs follow a two-tier structure:
1. Root: [proyecto/urls.py](proyecto/urls.py) includes app URLs
2. App level: [tienda/urls.py](tienda/urls.py) defines app-specific routes
   - Main store accessible at `/tienda/` (not root `/`)
   - Pattern: `path('tienda/', include('tienda.urls'))`

## Template Structure
Templates use Django's inheritance pattern:
- **Base**: [tienda/templates/tienda/base.html](tienda/templates/tienda/base.html) - Contains navigation header with logo, search bar, login/register buttons
- **Pages**: Extend base using `{% extends "tienda/base.html" %}`
- **Static files**: Load with `{% load static %}` at template top
- App templates must be in `tienda/templates/tienda/` (app-namespaced)

## Static Files Configuration
- **Collection directory**: `STATIC_ROOT = BASE_DIR / 'staticfiles'` for production
- **Development dirs**: `STATICFILES_DIRS` includes `tienda/static/`
- **URL prefix**: `STATIC_URL = 'static/'`
- **Custom CSS**: Edit [tienda/static/css/custom.css](tienda/static/css/custom.css) directly - no compilation needed

## Media Files (User Uploads) Configuration
- **Storage location**: `MEDIA_ROOT = BASE_DIR / 'tienda' / 'static' / 'media'` - all uploads go here
- **URL prefix**: `MEDIA_URL = 'media/'` 
- **Image uploads**: Organized in `tienda/static/media/images/` via `upload_to='images/'` in ImageField
- **Access**: Media files served automatically in development via Django's static file handler
- **Image model**: Located in [tienda/models.py](tienda/models.py) with `ImageField(upload_to='images/')`

## Shipping Restrictions
- **Zona de envío**: Solo se vende/envía dentro de la provincia de Almería
- **País fijo**: Las direcciones deben guardarse siempre con país `España`
- **Validación de provincia**: El código postal de envío debe ser de Almería (`04xxx`)

## Key Conventions
1. **App registration**: Apps use `AppConfig` - see `'tienda.apps.TiendaConfig'` in `INSTALLED_APPS`
2. **View pattern**: Function-based views in [tienda/views.py](tienda/views.py) (e.g., `index` renders template with context dict)
3. **Spanish naming**: UI elements use Spanish (`Iniciar Sesión`, `Registrarse`, `Menú`)
4. **Models**: Located in [tienda/models.py](tienda/models.py) - includes Product, Category, Cart, CartItem, Image
5. **Product caching**: Products are cached in Redis for 5 minutes when visited
   - Cache key pattern: `product_{id}` (stored as `:1:product_{id}` in Redis)
   - Cache is invalidated automatically when product is edited or deleted
   - Improves performance by ~15x for product detail pages
6. **Variables estáticas**: Las constantes y listas estáticas del proyecto deben declararse en [tienda/vars.py](tienda/vars.py) y consumirse desde ahí

## Development Workflow
- **Python environment**: This project uses venv at `.venv/bin/python`. Always use `/home/daniel/projects/proyecto/proyecto2/proyecto/.venv/bin/python` when running Python commands
- **Redis**: Sessions and product cache are stored in Redis (db 1). Redis must be running on localhost:6379
  - Start Redis: `sudo systemctl start redis-server` (Linux) or `brew services start redis` (macOS)
  - For Arch Linux: `sudo systemctl start valkey` (uses valkey-cli instead of redis-cli)
  - Verify: `redis-cli ping` or `valkey-cli ping` (should return PONG)
  - Test product cache: `python test_product_cache.py`
  - See [REDIS_SETUP.md](REDIS_SETUP.md) for complete setup instructions
- **Run server**: `/home/daniel/projects/proyecto/proyecto2/proyecto/.venv/bin/python manage.py runserver`
- **Migrations**: `/home/daniel/projects/proyecto/proyecto2/proyecto/.venv/bin/python manage.py makemigrations && /home/daniel/projects/proyecto/proyecto2/proyecto/.venv/bin/python manage.py migrate`
  - **IMPORTANT**: If `makemigrations` appears to fail (exit code 130 or similar), ALWAYS check `tienda/migrations/` directory first - the migration file is often created successfully despite the error message
  - Before attempting to recreate migrations, verify if the file already exists
- **Static files**: `python manage.py collectstatic` (for production)
- **Admin**: Access at `/admin/` (not `/tienda/admin/`)
- **Main app URL**: http://localhost:8000/tienda/

## Critical Details
- Django 6.0.1 specific - use current Django patterns
- SQLite database committed (`db.sqlite3`) - migrations already applied
- Bootstrap requires JavaScript for modals/toggles (reference data-bs-* attributes in base.html)
- SECRET_KEY is development-only (contains 'insecure' marker)
- DEBUG=True - not production-ready
- Search for a virtual environment in the project files, if there is one use it, if not, create it.

## When Adding Features
- New models: Add to [tienda/models.py](tienda/models.py), run migrations, register in [tienda/admin.py](tienda/admin.py)
- New views: Add to [tienda/views.py](tienda/views.py), register route in [tienda/urls.py](tienda/urls.py)
- New templates: Create in `tienda/templates/tienda/`, extend `base.html`
- Static assets: Place in `tienda/static/` subdirectories (css/, img/, js/)

## Seller Panel (Panel de Vendedor)
- **URL Base**: `/tienda/venta/` - All seller-related features under this path
- **Main Page**: `/tienda/venta/` - Lists all products created by the authenticated user
- **Create Product**: `/tienda/venta/crear-producto/` - Form to create new products
- **Header Button**: "Panel Vendedor" - Links to the seller main page (mis_productos view)
- **Concept**: Centralized area for sellers to manage their products (list, create, and future: edit, delete, analytics)

## Working Pattern with Developer
- **"Lo recuerdes"**: When the developer says to remember something, document it in this file immediately
- Update this file as the source of truth for project-specific decisions and patterns
