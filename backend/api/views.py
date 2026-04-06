from django.db.models import F, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import PageNumberPaginationWithLimit
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    RecipeCreateUpdateSerializer,
    RecipeListSerializer,
    ShoppingCartSerializer,
    SubscribeCreateSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeComposition,
    ShoppingCart,
    Tag
)
from users.models import Subscription, User


class UserAccountViewSet(UserViewSet):
    """ViewSet для управления пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPaginationWithLimit

    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        """
        Переопределяет метод me для ограничения доступа.

        Djoser предоставляет GET, PUT, PATCH, DELETE для /users/me/.
        Ограничивает только GET.
        """
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def update_avatar(self, request):
        """Обновляет аватар текущего пользователя."""
        user = request.user
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data['avatar']
        user.save()
        return Response({'avatar': user.avatar.url})

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар текущего пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        subscriptions = Subscription.objects.filter(user=request.user)
        authors = [sub.author for sub in subscriptions]
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписывается на пользователя."""
        author = self.get_object()
        serializer = SubscribeCreateSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отписывается от пользователя."""
        author = self.get_object()
        deleted_count, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()

        if not deleted_count:
            return Response(
                {'errors': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для тегов.

    Доступен всем пользователям без авторизации.
    Поддерживает только чтение.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для ингредиентов.

    Доступен всем пользователям без авторизации.
    Поддерживает поиск по названию с приоритетом на начало названия.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для рецептов.

    Поддерживает:
    - CRUD операции (создание/изменение только для авторизованных)
    - Фильтрацию по автору, тегам, избранному и списку покупок
    - Добавление/удаление в избранное и список покупок
    - Генерацию коротких ссылок
    - Выгрузку списка покупок
    """

    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related(
        'tags', 'ingredients__ingredient'
    )
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = PageNumberPaginationWithLimit

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer

        return RecipeListSerializer

    def perform_create(self, serializer):
        """Сохраняет рецепт у автора."""
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def add_favorite(self, request, pk=None):
        """Добавляет рецепт в избранное."""
        recipe = self.get_object()
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        recipe = self.get_object()
        deleted_count, _ = Favorite.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if not deleted_count:
            return Response(
                {'errors': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def add_shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок."""
        recipe = self.get_object()
        serializer = ShoppingCartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок."""
        recipe = self.get_object()
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if not deleted_count:
            return Response(
                {'errors': 'Рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Скачивает список покупок в формате txt.

        Суммирует ингредиенты из всех рецептов в корзине пользователя.
        Возвращает файл с чекбоксами для удобства использования.
        """
        shopping_cart = ShoppingCart.objects.filter(user=request.user)

        if not shopping_cart.exists():
            return Response(
                {'errors': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = self._collect_ingredients(shopping_cart)
        return self._generate_txt(ingredients)

    def _collect_ingredients(self, shopping_cart):
        """
        Собирает и суммирует ингредиенты из корзины.
        """
        recipe_ids = shopping_cart.values_list('recipe_id', flat=True)

        ingredients_data = RecipeComposition.objects.filter(
            recipe_id__in=recipe_ids
        ).values(
            ingredient_name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient_name')

        return [
            {
                'name': item['ingredient_name'],
                'amount': item['total_amount'],
                'unit': item['measurement_unit']
            }
            for item in ingredients_data
        ]

    def _generate_txt(self, ingredients_dict):
        """Генерирует TXT файл с чекбоксами."""
        content_lines = ['Список покупок:\n']
        for item in ingredients_dict:
            content_lines.append(
                f'☐ {item["name"]} — {item["amount"]} {item["unit"]}'
            )
        content = '\n'.join(content_lines)

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Генерирует и возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()

        domain = request.build_absolute_uri('/')[:-1]
        short_url = f'{domain}/s/{recipe.short_link}'

        return Response({'short-link': short_url})


def redirect_to_recipe(request, code):
    """Редирект по короткой ссылке на страницу рецепта."""
    recipe = get_object_or_404(Recipe, short_link=code)

    return HttpResponseRedirect(f'/recipes/{recipe.id}/')
