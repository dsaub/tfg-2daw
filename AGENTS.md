# AGENTS.md - Django Tienda Project

## Commands

```bash
# Run tests (runs tienda/tests.py by default)
make test

# Or manually
python manage.py test

# Run dev server
python manage.py runserver

# Run migrations
python manage.py migrate

# Static files (production)
python manage.py collectstatic
```

## Prerequisites

- **Redis**: Must be running on `redis://127.0.0.1:6379/1` for sessions and caching
  - Start: `sudo systemctl start redis-server` (Linux) or `brew services start redis` (macOS)
  - Verify: `redis-cli ping` → PONG
- **PostgreSQL**: Default database; set `POSTGRES_ENABLED=False` to use SQLite
- **Environment**: Copy `.env.example` to `.env` and configure required vars

## Important Quirks

1. **Migrations**: If `makemigrations` fails with error code 130, **check `tienda/migrations/`** - the file is often created despite the error
2. **Test DB**: Uses SQLite regardless of POSTGRES_ENABLED (hardcoded in settings.py)
3. **App URL**: Not at `/` - access at `http://localhost:8000/tienda/`
4. **Admin**: At `/admin/` (not `/tienda/admin/`)
5. **Custom User Model**: AUTH_USER_MODEL = 'tienda.User' - use for all user-related queries

## Architecture

- `proyecto/` - Django settings, URLs, WSGI/ASGI
- `tienda/` - Main app (models, views, admin, templates)
- `tienda/static/` - CSS, JS, images, fonts
- Templates extend `tienda/templates/tienda/base.html`

## Shipping Restrictions

Only sells to Almería province, Spain (postal codes 04xxx). All addresses saved with country "España".

## External Services

- **Payment**: Stripe + PayPal (configured via .env)
- **Storage**: S3 support - set `S3_ENABLE=True` to enable
- **Email**: SMTP required (see .env.example)
- **Async**: Celery uses Redis broker

## Useful References

- Full developer docs: `.github/copilot-instructions.md`
- Redis setup: `docs/REDIS_SETUP.md`
- PayPal: `docs/PAYPAL_SETUP.md`, `docs/PAYPAL_TROUBLESHOOTING.md`
- View documentation: `docs/views/`