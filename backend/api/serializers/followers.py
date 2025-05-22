"""
from rest_framework import serializers
from users.models import Follow
from .users import CustomUserSerializer

# CHECKED


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['user', 'author']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Подписка на этого автора уже существует'
            )
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Создание подписки на самого себя невозможно'
            )
        return data

    def to_representation(self, instance):
        return CustomUserSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data
"""