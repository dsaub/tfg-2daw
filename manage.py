#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proyecto.settings")

    # Si se ejecuta `manage.py test` sin labels, limitar a pruebas de tienda/tests.py.
    if len(sys.argv) >= 2 and sys.argv[1] == "test":
        has_test_labels = any(not arg.startswith("-") for arg in sys.argv[2:])
        if not has_test_labels:
            sys.argv.append("tienda.tests")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
