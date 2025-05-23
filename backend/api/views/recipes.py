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
    """API endpoint for managing ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientSearchFilter
    search_fields = ['^name']
    pagination_class = None


class RecipeAPIViewSet(viewsets.ModelViewSet):
    """API endpoint for managing recipes."""

    queryset = Recipe.objects.select_related(
        'author').prefetch_related('ingredients')
    filterset_class = RecipeFilter
    filter_backends = [DjangoFilterBackend]
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['list', 'retrieve']:
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        """Set the recipe author to the current user."""
        serializer.save(author=self.request.user)

    def _manage_recipe_action(self, request, recipe_id, model,
                              serializer_class, error_msg):
        """Generic handler for recipe-related actions.

        Args:
            request: HTTP request object
            recipe_id: ID of the recipe
            model: Model class to interact with
            serializer_class: Serializer to use
            error_msg: Error message for failed operations

        Returns:
            Response with appropriate status code
        """
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
            return Response(
                {'detail': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def favorite_action(self, request, pk=None):
        """Add/remove recipe from favorites.

        Args:
            request: HTTP request object
            pk: Recipe ID

        Returns:
            Response with appropriate status code
        """
        return self._manage_recipe_action(
            request, pk,
            Favorite, FavoriteSerializer,
            'Recipe not found in favorites'
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart'
    )
    def shopping_cart_action(self, request, pk=None):
        """Manage shopping cart items.

        Args:
            request: HTTP request object
            pk: Recipe ID

        Returns:
            Response with appropriate status code
        """
        return self._manage_recipe_action(
            request, pk,
            ShoppingCart, ShoppingCartSerializer,
            'Recipe not found in shopping cart'
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def export_shopping_list(self, request):
        """Export shopping list in specified format.

        Args:
            request: HTTP request object

        Returns:
            Shopping list in requested format (PDF/TXT)
        """
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
                {'message': 'Shopping list is empty'},
                status=status.HTTP_200_OK
            )

        export_format = request.query_params.get('format', 'pdf')
        if export_format == 'txt':
            return generate_text_shopping_list(ingredients, user)
        return generate_pdf_shopping_list(ingredients, user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_short_link(self, request, pk=None):
        """Get short URL for a recipe.

        Args:
            request: HTTP request object
            pk: Recipe ID

        Returns:
            Response containing short URL code
        """
        recipe = self.get_object()
        return Response({
            'short-link': recipe.short_code
        })
