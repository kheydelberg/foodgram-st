from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views.users import CustomUserViewSet
from api.views.recipes import RecipeAPIViewSet, IngredientAPIViewSet
from api.views.redirect import resolve_short_link

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('recipes', RecipeAPIViewSet, basename='recipes')
router.register('ingredients', IngredientAPIViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('s/<slug:slug>/', resolve_short_link, name='recipe_short_link'),
]
