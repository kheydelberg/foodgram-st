from rest_framework import serializers

from recipes.models import Recipe
from users.models import Follow
from api.serializers.users import CustomUserSerializer


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Compact serializer for recipe representation in subscriptions.

    Includes only essential fields for lightweight display.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating and validating user subscriptions."""

    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'author'],
                message='You are already subscribed to this author'
            )
        ]

    def validate_subscription(self, attrs):
        """Prevent users from subscribing to themselves.

        Args:
            attrs (dict): Input attributes including user and author

        Returns:
            dict: Validated attributes

        Raises:
            ValidationError: If user tries to subscribe to themselves
        """
        if attrs['user'] == attrs['author']:
            raise serializers.ValidationError(
                'Cannot subscribe to yourself'
            )
        return attrs

    def create_response(self, instance):
        """Generate subscription response using detail serializer.

        Args:
            instance (Follow): Subscription instance

        Returns:
            dict: Serialized author data with recipes
        """
        return FollowDetailSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data

    def validate(self, attrs):
        """Main validation method for subscription."""
        return self.validate_subscription(attrs)

    def to_representation(self, instance):
        """Transform subscription instance
        into detailed author representation."""
        return self.create_response(instance)


class FollowDetailSerializer(CustomUserSerializer):
    """Detailed serializer for subscribed authors including their recipes.

    Extends UserSerializer with recipe-related fields for comprehensive
    subscription view.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + \
            ['recipes', 'recipes_count']

    def get_user_recipes(self, author, limit=None):
        """Retrieve recipes for given author with optional limit.

        Args:
            author (CustomUser): Author to get recipes for
            limit (int, optional): Maximum number of recipes to return

        Returns:
            list: Serialized recipe data
        """
        queryset = author.recipes.all()
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except (ValueError, TypeError):
                pass
        return ShortRecipeSerializer(
            queryset, many=True, context=self.context
        ).data

    def count_user_recipes(self, author):
        """Count total recipes for given author.

        Args:
            author (CustomUser): Author to count recipes for

        Returns:
            int: Number of recipes
        """
        return author.recipes.count()

    def get_recipes(self, obj):
        """Serializer method for recipes field with query limit support."""
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        return self.get_user_recipes(obj, limit)

    def get_recipes_count(self, obj):
        """Serializer method for recipes_count field."""
        return self.count_user_recipes(obj)
