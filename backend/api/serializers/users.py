from djoser.serializers import UserSerializer as BaseUserSerializer
from .redefined_base64 import Base64ImageField
from rest_framework import serializers

from users.models import CustomUser


class CustomUserSerializer(BaseUserSerializer):
    """Serializer for user data handling including
    registration and profile viewing.

    Extends the base Djoser user serializer with
    additional fields and custom validation.
    Handles:
    - User registration
    - Profile serialization
    - Subscription status checking
    """

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(required=True, max_length=300)

    class Meta(BaseUserSerializer.Meta):
        model = CustomUser
        fields = [
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar', 'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def perform_create(self, validated_data):
        """Create a new user instance with hashed password."""
        user_password = validated_data.pop('password')
        new_user = CustomUser(**validated_data)
        new_user.set_password(user_password)
        new_user.save()
        return new_user

    def check_email_uniqueness(self, email):
        """Verify if email is already registered.

        Args:
            email (str): Email address to check

        Returns:
            str: Valid email if not registered

        Raises:
            ValidationError: If email already exists
        """
        if (CustomUser.objects.filter(email=email).exists()
                and self.context.get('request').method == 'POST'):
            raise serializers.ValidationError(
                'This email is already registered'
            )
        return email

    def get_subscription_status(self, user):
        """Check if current user is subscribed to the given user.

        Args:
            user (CustomUser): User to check subscription for

        Returns:
            bool: True if subscribed, False otherwise
        """
        current_user = self.context.get('request').user
        return (current_user.is_authenticated
                and current_user.follower.filter(author=user).exists())

    def format_response(self, instance):
        """Format the serialized response removing sensitive data.

        Args:
            instance (CustomUser): User instance to serialize

        Returns:
            dict: Serialized user data without password
        """
        response_data = super().to_representation(instance)
        if 'password' in response_data:
            del response_data['password']
        return response_data

    def validate_email(self, value):
        """Validate email field ensuring uniqueness."""
        return self.check_email_uniqueness(value)

    def get_is_subscribed(self, user):
        """Serializer method for is_subscribed field."""
        return self.get_subscription_status(user)

    def create(self, validated_data):
        """Create and return new user instance."""
        return self.perform_create(validated_data)

    def to_representation(self, instance):
        """Customize response format based on request context.

        Returns simplified response for registration endpoint,
        full profile data for other requests.
        """
        request = self.context.get('request')
        if (
            request and request.method == 'POST'
                and request.path.endswith('/api/users/')
        ):
            return {
                'id': instance.id,
                'username': instance.username,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'email': instance.email,
            }
        return self.format_response(instance)


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user avatar image.

    Handles base64 encoded image uploads and returns full URL in response.
    """

    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)

    def get_avatar_url(self, user):
        """Generate absolute URL for user's avatar.

        Args:
            user (CustomUser): User instance

        Returns:
            str: Absolute URL to avatar image or None if not set
        """
        if not user.avatar:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(user.avatar.url)
        else:
            return user.avatar.url

    def to_representation(self, instance):
        """Return avatar URL in response."""
        return {'avatar': self.get_avatar_url(instance)}
