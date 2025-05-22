from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import display
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import CustomUser, Follow

# CHECKED


class CustomUserAdminConfig(UserAdmin):

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            total_recipes=Count('recipes', distinct=True),
            total_followers=Count('follower', distinct=True)
        )

    @display(description=_('Recipes'))
    def recipe_amount(self, obj):
        return getattr(obj, 'total_recipes', 0)

    @display(description=_('Followers'))
    def follower_amount(self, obj):
        return getattr(obj, 'total_followers', 0)

    list_config = {
        'display': ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'recipe_amount', 'follower_amount'),
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
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions')
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


class FollowAdminPanel(admin.ModelAdmin):

    list_config = {
        'display': ('user', 'author'),
        'search': ('user__username', 'author__username'),
        'filter': ()
    }

    def get_list_display(self, request):
        return self.list_config['display']

    def get_search_fields(self, request):
        return self.list_config['search']

    def get_list_filter(self, request):
        return self.list_config['filter']


admin.site.register(CustomUser, CustomUserAdminConfig)
admin.site.register(Follow, FollowAdminPanel)
