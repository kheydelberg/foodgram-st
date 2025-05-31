from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from djoser.views import UserViewSet as BaseUserViewSet
from users.models import CustomUser
from api.serializers.users import AvatarUpdateSerializer
from api.serializers.followers import (
    FollowDetailSerializer,
    FollowCreateSerializer
)


class CustomUserViewSet(BaseUserViewSet):
    """Custom viewset for user management with extended functionality."""

    def get_permissions(self):
        """Set permissions based on action."""
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
        """Handle follow/unfollow actions.

        Args:
            request: HTTP request object
            id: ID of user to follow/unfollow

        Returns:
            Response with appropriate status code
        """
        follower = request.user
        following = get_object_or_404(CustomUser, id=id)

        if request.method == 'POST':
            return self._create_follow(follower, following)
        return self._remove_follow(follower, following)

    def _create_follow(self, follower, following):
        """Create a follow relationship between users.

        Args:
            follower: User who is following
            following: User being followed

        Returns:
            Response with subscription data (201) or error (400)
        """
        recipes_limit = self.request.query_params.get('recipes_limit')

        serializer = FollowCreateSerializer(data={
            'user': follower.id,
            'author': following.id
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_serializer = FollowDetailSerializer(
            following,
            context={
                'request': self.request,
                'recipes_limit': recipes_limit
            }
        )
        return Response(
            user_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def _remove_follow(self, follower, following):
        """Remove a follow relationship.

        Args:
            follower: User who is unfollowing
            following: User being unfollowed

        Returns:
            Response with status code (204) or error (400)
        """
        deleted, _ = follower.follower.filter(author=following).delete()

        if not deleted:
            return Response(
                {'detail': 'Subscription not found'},
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
        """Retrieve list of user subscriptions.

        Args:
            request: HTTP request object

        Returns:
            Paginated response with subscription data
        """
        authors = CustomUser.objects.filter(
            following__user=request.user
        ).prefetch_related('recipes')
        page = self.paginate_queryset(authors)

        serializer = FollowDetailSerializer(
            page if page is not None else authors,
            many=True,
            context={
                'request': request,
                'recipes_limit': request.query_params.get('recipes_limit')
            }
        )

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def update_avatar(self, request):
        """Handle avatar updates and deletions.

        Args:
            request: HTTP request object

        Returns:
            Response with appropriate status code
        """
        user_profile = request.user

        if request.method == 'PUT':
            return self._update_profile_picture(user_profile, request)
        return self._clear_profile_picture(user_profile)

    def _update_profile_picture(self, user, request):
        """Update user profile picture.

        Args:
            user: User object to update
            request: HTTP request object

        Returns:
            Response with updated user data or error
        """
        if 'avatar' not in request.data:
            return Response(
                {'avatar': ['Image file is required']},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AvatarUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def _clear_profile_picture(self, user):
        """Remove user profile picture.

        Args:
            user: User object to update

        Returns:
            Empty response with status code (204)
        """
        if user.avatar:
            user.avatar.delete()
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
