from django.db.models import Sum, F
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from api.filters import RecipeFilter, IngredientSearchFilter
from api.permissions import IsAuthorOrReadOnly
from recipes.models import (
    Ingredient, Recipe, Favorite, ShoppingCart,
    RecipeIngredient
)
from api.serializers.recipes import (
    IngredientSerializer, RecipeListSerializer,
    RecipeCreateUpdateSerializer, FavoriteSerializer,
    ShoppingCartSerializer
)

from api.utils import generate_pdf_shopping_list, generate_text_shopping_list


class IngredientAPIViewSet(viewsets.ReadOnlyModelViewSet):
    """API для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientSearchFilter
    search_fields = ['^name']
    pagination_class = None


class RecipeAPIViewSet(viewsets.ModelViewSet):
    """API для управления рецептами."""

    queryset = Recipe.objects.select_related(
        'author').prefetch_related('ingredients')
    filterset_class = RecipeFilter
    filter_backends = [DjangoFilterBackend]
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _manage_recipe_action(self, request, recipe_id, model,
                              serializer_class, error_msg):
        """Общий обработчик действий с рецептами."""
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = request.user

        if request.method == 'POST':
            context = {'request': request}
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = serializer_class(data=data, context=context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            return Response({'detail': error_msg},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def favorite_action(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        return self._manage_recipe_action(
            request, pk,
            Favorite, FavoriteSerializer,
            'Рецепт отсутствует в избранном'
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart'
    )
    def shopping_cart_action(self, request, pk=None):
        """Управление списком покупок."""
        return self._manage_recipe_action(
            request, pk,
            ShoppingCart, ShoppingCartSerializer,
            'Рецепт отсутствует в списке покупок'
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def export_shopping_list(self, request):
        """Экспорт списка покупок."""
        user = request.user
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=user)
            .values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit')
            )
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )

        if not ingredients:
            return Response(
                {'message': 'Список покупок пуст'},
                status=status.HTTP_200_OK
            )

        format = request.query_params.get('format', 'pdf')
        if format == 'txt':
            return generate_text_shopping_list(ingredients, user)
        return generate_pdf_shopping_list(ingredients, user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        return Response({
            'short-link': recipe.short_code
        })
