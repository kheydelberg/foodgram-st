from django.db import transaction as db_transaction
from rest_framework import serializers

from api.serializers.users import CustomUserSerializer
from .redefined_base64 import Base64ImageField
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart
)

from api.consts import (
    MAX_COOKING_TIME,
    MAX_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT
)

from api.mixins import (
    RecipeValidationMixin,
    IngredientHandlingMixin,
    UserRelationCheckMixin
)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient model representation."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating recipe ingredient components."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        max_value=MAX_INGREDIENT_AMOUNT
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for recipe ingredient components display."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(
    UserRelationCheckMixin,
    serializers.ModelSerializer
):
    """Serializer for displaying list of recipes."""

    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        """Check if recipe is in user's favorites."""
        return self._check_user_relation(obj, 'favorites')

    def get_is_in_shopping_cart(self, obj):
        """Check if recipe is in user's shopping cart."""
        return self._check_user_relation(obj, 'shopping_carts')


class RecipeCreateUpdateSerializer(
    serializers.ModelSerializer,
    RecipeValidationMixin,
    IngredientHandlingMixin
):
    """Serializer for recipe creation and modification."""

    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time'
        )

    def validate(self, attrs):
        """Validate all input data."""
        attrs = super().validate(attrs)
        components = attrs.get('ingredients')
        self.validate_ingredients(components)
        return attrs

    @db_transaction.atomic
    def create(self, validated_attrs):
        """Create new recipe with ingredients."""
        components = validated_attrs.pop('ingredients')
        recipe = Recipe.objects.create(**validated_attrs)
        self._add_components(recipe, components)
        return recipe

    @db_transaction.atomic
    def update(self, instance, validated_attrs):
        """Update recipe and its ingredients."""
        components = validated_attrs.pop('ingredients')
        instance.recipe_ingredients.all().delete()
        self._add_components(instance, components)
        return super().update(instance, validated_attrs)

    def to_representation(self, instance):
        """Return representation in list format."""
        return RecipeListSerializer(
            instance,
            context={'request': self.context['request']}
        ).data


class CompactRecipeSerializer(serializers.ModelSerializer):
    """Compact serializer for favorites and shopping cart."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart items."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Recipe already in shopping cart'
            )
        ]

    def to_representation(self, instance):
        """Return recipe representation."""
        return CompactRecipeSerializer(
            instance.recipe,
            context={'request': self.context['request']}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for favorite recipes."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Recipe already in favorites'
            )
        ]

    def to_representation(self, instance):
        """Return recipe representation."""
        return CompactRecipeSerializer(
            instance.recipe,
            context={'request': self.context['request']}
        ).data
