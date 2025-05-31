from django.db import transaction as db_transaction
from rest_framework import serializers

from recipes.models import RecipeIngredient


class RecipeValidationMixin:
    """Mixin for common recipe validations."""

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
        request = self.context['request']
        return (request.user.is_authenticated

                and getattr(request.user, relation_name).filter(
                    recipe=obj).exists()
                )
