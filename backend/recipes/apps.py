from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RecipesConfig(AppConfig):
    """Django application configuration for the recipes app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
    verbose_name = _('Recipes')
