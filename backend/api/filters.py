from django_filters import rest_framework as filters
from recipes.models import Recipe, Ingredient


class IngredientSearchFilter(filters.FilterSet):
    """Filter for ingredients with case-insensitive name search."""

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        """Meta options for IngredientSearchFilter."""

        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Advanced filter for recipes with favorite and shopping cart options."""

    is_favorited = filters.BooleanFilter(
        method='filter_favorite_recipes'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_cart_recipes'
    )

    class Meta:
        """Meta options for RecipeFilter."""

        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author')

    def filter_favorite_recipes(self, queryset, _, value):
        """Filter recipes based on user's favorites.

        Args:
            queryset: Original recipe queryset
            _: Unused filter parameter
            value: Boolean indicating whether to filter favorites

        Returns:
            Filtered queryset containing only favorited recipes
            if value is True
        """
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_cart_recipes(self, queryset, _, value):
        """Filter recipes based on user's shopping cart.

        Args:
            queryset: Original recipe queryset
            _: Unused filter parameter
            value: Boolean indicating whether to filter cart items

        Returns:
            Filtered queryset containing only cart recipes if value is True
        """
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_carts__user=user)
        return queryset
