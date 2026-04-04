from django.db.models import F, Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.filters import RecipeFilter, IngredientFilter
from api.pagination import PageNumberPaginationWithLimit
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    FavoriteSerializer,
    RecipeCreateUpdateSerializer,
    RecipeListSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeComposition,
    ShoppingCart,
    Tag
)


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
        if self.action == 'list':
            return RecipeListSerializer

        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer

        return RecipeListSerializer

    def perform_create(self, serializer):
        """Сохраняет рецепт у автора."""
        serializer.save(author=self.request.user)

    # Следующие три функции нужны для возврата ответа с полной информацией
    # в соответствии со спецификацией, без них тесты Postman падают
    def _get_full_recipe_response(self, recipe, status_code):
        """
        Формирует ответ с полными данными рецепта.
        """
        output_serializer = RecipeListSerializer(
            recipe,
            context={'request': self.request}
        )
        return Response(output_serializer.data, status=status_code)

    def create(self, request, *args, **kwargs):
        """
        Создает рецепт и возвращает ответ с полной информацией.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return self._get_full_recipe_response(
            serializer.instance,
            status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """
        Обновляет рецепт и возвращает ответ с полной информацией.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return self._get_full_recipe_response(
            serializer.instance,
            status.HTTP_200_OK
        )

    def _add_or_remove_relation(
            self, request, pk, serializer_class, model, error_remove
    ):
        """
        Добавляет или удаляет связь между пользователем и рецептом.

        Используется для:
        - избранного (Favorite)
        - списка покупок (ShoppingCart)
        """
        recipe = self.get_object()

        if request.method == 'POST':
            serializer = serializer_class(
                data={},
                context={'request': request, 'recipe': recipe}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'errors': error_remove},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

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
            data={},
            context={'request': request, 'recipe': recipe}
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
        if deleted_count == 0:
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
            data={},
            context={'request': request, 'recipe': recipe}
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
        if deleted_count == 0:
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
