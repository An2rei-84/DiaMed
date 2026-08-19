"""ASGI config for DiaMed project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diamed.settings")

application = get_asgi_application()
