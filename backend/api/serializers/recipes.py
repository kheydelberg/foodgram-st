from django.db import transaction as db_transaction
from rest_framework import serializers

from api.serializers.users import CustomUserSerializer
from .redefined_base64 import Base64ImageField
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart
)


class RecipeValidationMixin:
    """Mixin for common recipe validations."""

    def validate_cooking_time(self, duration):
        """Validate cooking time constraints."""
        if duration < 1:
            raise serializers.ValidationError(
                f'Cooking time must be at least {1} minute'
            )
        if duration > 1000:
            raise serializers.ValidationError(
                'Cooking time is too long'
            )
        return duration

    def validate_image(self, img):
        """Validate image presence."""
        if not img:
            raise serializers.ValidationError('Image is required')
        return img


class IngredientHandlingMixin:
    """Mixin for handling recipe ingredients."""

    @db_transaction.atomic
    def _add_components(self, recipe, components):
        """Bulk create recipe ingredients."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=component['id'],
                amount=component['amount']
            ) for component in components
        )

    def validate_ingredients(self, components):
        """Validate ingredients requirements."""
        if not components:
            raise serializers.ValidationError(
                {'ingredients': 'At least one ingredient is required'}
            )

        component_ids = [item['id'].id for item in components]
        if len(component_ids) != len(set(component_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ingredients must be unique'}
            )
        return components


class UserRelationCheckMixin:
    """Mixin for checking user-recipe relationships."""

    def _check_user_relation(self, obj, relation_name):
        """Check if recipe exists in user's related model."""
        req = self.context.get('request')
        return (req and req.user.is_authenticated
                and getattr(obj, relation_name).filter(user=req.user).exists())


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
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        """Ensure the amount meets minimum requirements."""
        min_value = 1
        if value < min_value:
            raise serializers.ValidationError(
                f'Ingredient quantity must be at least {min_value}'
            )
        return value


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
    cooking_time = serializers.IntegerField()

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
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self._add_components(instance, components)
        return super().update(instance, validated_attrs)

    def to_representation(self, instance):
        """Return representation in list format."""
        return RecipeListSerializer(
            instance,
            context={'request': self.context.get('request')}
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
            context={'request': self.context.get('request')}
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
            context={'request': self.context.get('request')}
        ).data
