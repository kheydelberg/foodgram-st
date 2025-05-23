from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import display
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import CustomUser, Follow


class CustomUserAdminConfig(UserAdmin):
    """Custom admin configuration for the CustomUser model."""

    def get_queryset(self, request):
        """Annotate queryset with recipe and follower counts."""
        return super().get_queryset(request).annotate(
            total_recipes=Count('recipes', distinct=True),
            total_followers=Count('follower', distinct=True)
        )

    @display(description=_('Recipes'))
    def recipe_amount(self, obj):
        """Display the number of recipes for a user."""
        return getattr(obj, 'total_recipes', 0)

    @display(description=_('Followers'))
    def follower_amount(self, obj):
        """Display the number of followers for a user."""
        return getattr(obj, 'total_followers', 0)

    list_config = {
        'display': (
            'username', 'email', 'first_name', 'last_name',
            'is_staff', 'recipe_amount', 'follower_amount'
        ),
        'filter': ('is_staff', 'is_superuser', 'is_active', 'date_joined'),
        'search': ('username__icontains', 'email__icontains'),
        'ordering': ('-date_joined',)
    }

    section_fields = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'avatar')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


class FollowAdminPanel(admin.ModelAdmin):
    """Admin configuration for the Follow model."""

    list_config = {
        'display': ('user', 'author'),
        'search': ('user__username', 'author__username'),
        'filter': ()
    }

    def get_list_display(self, request):
        """Return fields to display in the list view."""
        return self.list_config['display']

    def get_search_fields(self, request):
        """Return fields to search in the admin interface."""
        return self.list_config['search']

    def get_list_filter(self, request):
        """Return fields to filter by in the admin interface."""
        return self.list_config['filter']


admin.site.register(CustomUser, CustomUserAdminConfig)
admin.site.register(Follow, FollowAdminPanel)
