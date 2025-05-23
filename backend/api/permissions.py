from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Permission to allow only authors to edit their own content."""

    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access the object.

        Args:
            request: The incoming request
            view: The view handling the request
            obj: The object being accessed

        Returns:
            bool: True if safe method or user is author, False otherwise
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
