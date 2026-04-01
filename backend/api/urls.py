from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet
from users.views import CustomUserViewSet

router_v1 = DefaultRouter()

router_v1.register('users', CustomUserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns += [
    path(
        'recipes/by-tag/<slug:tag_slug>/',
        RecipeViewSet.as_view({'get': 'by_tag'}),
        name='recipes-by-tag'
    ),
    path(
        'recipes/by-tags/',
        RecipeViewSet.as_view({'get': 'by_tags'}),
        name='recipes-by-tags'
    ),
]
