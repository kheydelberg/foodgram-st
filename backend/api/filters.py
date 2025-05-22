from django_filters import rest_framework as filters
from recipes.models import Recipe, Ingredient

# CHECKED


class IngredientSearchFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(
        method='filter_favorite_recipes'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_cart_recipes'
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author')

    def filter_favorite_recipes(self, queryset, _, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_cart_recipes(self, queryset, _, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_carts__user=user)
        return queryset
