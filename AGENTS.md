# AGENTS.md - Django Tienda Project

## Commands

```bash
make test           # Run tests
python manage.py runserver   # Dev server
python manage.py migrate     # Migrations
python manage.py collectstatic  # Static files (production)
```

## Prerequisites

- **Redis**: `redis://127.0.0.1:6379/1` (Linux: `sudo systemctl start redis-server`)
- **PostgreSQL**: Default. Set `POSTGRES_ENABLED=False` for SQLite
- **Environment**: Copy `.env.example` to `.env`

## Quirks

1. **Migrations**: If `makemigrations` fails with error 130, check `tienda/migrations/` - file often created anyway
2. **Test DB**: Always uses SQLite (hardcoded)
3. **App URL**: `http://localhost:8000/tienda/` (not `/`)
4. **Admin**: `/admin/`
5. **User Model**: Use `tienda.User` for queries

## Architecture

- `proyecto/` - Django settings, URLs, WSGI/ASGI
- `tienda/` - Main app (models, views, admin, templates)
- Templates extend `tienda/templates/tienda/base.html`

## Shipping

Only Almería province, Spain (04xxx). Country: "España".

## External Services

- **Payment**: Stripe + PayPal (via .env)
- **Storage**: S3 - set `S3_ENABLE=True`
- **Email**: SMTP (see .env.example)
- **Async**: Celery + Redis

## Deploy

- Push to `origin` and `github` after changes
- GitHub Actions updates `ghcr.io/dsaub/proyecto-mvc:development`
- SSH: `debian@172.16.14.221` (requires VPN - skip if unavailable)
- Stack: `/home/debian/composes/mvc/mvc.yml` on swarm
- Timeout: 1 minute max when updating services
- Docker job requires Test job to pass first

## Other

- **Repo**: https://github.com/dsaub/proyecto-final
- **Python**: 3.14, use `.venv` virtualenv
- **GIT**: origin → git.elordenador.org, github → GitHub
- **Docs**: `.github/copilot-instructions.md`, `docs/`