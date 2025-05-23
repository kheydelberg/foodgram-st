from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import display
from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)


class RecipeIngredientInline(admin.TabularInline):
    """Inline admin interface for RecipeIngredient model."""

    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = _('ingredient')
    verbose_name_plural = _('ingredients')


class IngredientAdmin(admin.ModelAdmin):
    """Admin interface for Ingredient model."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeAdmin(admin.ModelAdmin):
    """Admin interface for Recipe model with favorites count."""

    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('author', 'name')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('favorites_count',)

    @display(description=_('Added to favorites'))
    def favorites_count(self, obj):
        """Return count of how many times recipe was added to favorites."""
        return obj.favorites.count()


class FavoriteAdmin(admin.ModelAdmin):
    """Admin interface for Favorite model."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    verbose_name = _('favorite')
    verbose_name_plural = _('favorites')


class ShoppingCartAdmin(admin.ModelAdmin):
    """Admin interface for ShoppingCart model."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    verbose_name = _('shopping cart item')
    verbose_name_plural = _('shopping cart items')


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
