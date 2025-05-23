from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ApiConfig(AppConfig):
    """Django application configuration for the API app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = _('API')
