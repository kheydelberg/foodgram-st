from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, AllowAny
from rest_framework.response import Response
from djoser.views import UserViewSet as BaseUserViewSet
from users.models import CustomUser
from users.models import Follow
from api.serializers.users import (
    UserSubscriptionSerializer,
    SetAvatarSerializer,
    UserSubscriptionSerializer,
    FollowSerializer
)


class CustomUserViewSet(BaseUserViewSet):
    """Кастомный вьюсет для работы с пользователями."""

    def get_permissions(self):
        if self.action in ["retrieve", "list"]:
            return [AllowAny()]
        return super().get_permissions()

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def follow(self, request, id=None):
        """Обработка подписки/отписки."""
        follower = request.user
        following = get_object_or_404(CustomUser, id=id)

        if request.method == 'POST':
            return self._create_follow(follower, following)
        return self._remove_follow(follower, following)

    def _create_follow(self, follower, following):
        """Логика создания подписки."""
        recipes_limit = self.request.query_params.get('recipes_limit')

        # Создаем подписку
        serializer = FollowSerializer(data={
            'user': follower.id,
            'author': following.id
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Возвращаем данные пользователя с рецептами
        user_serializer = UserSubscriptionSerializer(
            following,
            context={
                'request': self.request,
                'recipes_limit': recipes_limit
            }
        )
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)

    def _remove_follow(self, follower, following):
        """Логика удаления подписки."""
        deleted, _ = Follow.objects.filter(
            user=follower,
            author=following
        ).delete()

        if not deleted:
            return Response(
                {'detail': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def following(self, request):
        """Получение списка подписок."""
        authors = CustomUser.objects.filter(
            following__user=request.user
        ).prefetch_related('recipes')  # Оптимизация запроса
        page = self.paginate_queryset(authors)

        serializer = UserSubscriptionSerializer(
            page if page is not None else authors,
            many=True,
            context={
                'request': request,
                # Передаем параметр
                'recipes_limit': request.query_params.get('recipes_limit')
            }
        )

        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def update_avatar(self, request):
        """Обновление аватара профиля."""
        user_profile = request.user

        if request.method == 'PUT':
            return self._update_profile_picture(user_profile, request)
        return self._clear_profile_picture(user_profile)

    def _update_profile_picture(self, user, request):
        """Обновление изображения профиля."""
        if 'avatar' not in request.data:
            return Response(
                {'avatar': ['Необходимо указать изображение']},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SetAvatarSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def _clear_profile_picture(self, user):
        """Удаление изображения профиля."""
        if user.avatar:
            user.avatar.delete()
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
