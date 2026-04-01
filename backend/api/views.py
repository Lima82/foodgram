import csv

from django.db.models import BooleanField, Case, Value, When
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.pagination import CustomPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeDetailSerializer,
    RecipeListSerializer,
    ShortRecipeSerializer,
    TagSerializer,
)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from recipes.utils import generate_short_code


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

    def get_queryset(self):
        """
        Фильтрует ингредиенты по параметру name.

        Для одного символа - только начинающиеся с этого символа.
        Для двух и более - поиск по вхождению с сортировкой:
        сначала те, что начинаются с искомой строки, затем остальные.
        """
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')

        if name:
            if len(name) == 1:
                queryset = queryset.filter(name__istartswith=name)
            else:
                queryset = queryset.annotate(
                    starts_with=Case(
                        When(name__istartswith=name, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                )
                queryset = queryset.filter(name__icontains=name)
                queryset = queryset.order_by('-starts_with', 'name')

        return queryset


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

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия."""
        if self.action == 'list':
            return RecipeListSerializer
        if self.action in ('update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        if self.action == 'create':
            return RecipeCreateUpdateSerializer

        return RecipeDetailSerializer

    def get_queryset(self):
        """Фильтрует рецепты по параметрам запроса."""
        # queryset = Recipe.objects.all()
        # is_favorited = self.request.query_params.get('is_favorited')
        # is_in_shopping_cart = self.request.query_params.get(
        #     'is_in_shopping_cart'
        # )
        # # author = self.request.query_params.get('author')
        # # tags = self.request.query_params.getlist('tags')

        # if is_favorited == '1' and self.request.user.is_authenticated:
        #     queryset = queryset.filter(favorites__user=self.request.user)
        # if is_in_shopping_cart == '1' and self.request.user.is_authenticated:
        #     queryset = queryset.filter(shopping_cart__user=self.request.user)
        # # if author:
        # #     queryset = queryset.filter(author_id=author)
        # # if tags:
        # #     queryset = queryset.filter(tags__slug__in=tags).distinct()

        # return queryset.select_related('author').prefetch_related(
        #     'tags', 'ingredients__ingredient'
        # )
        queryset = Recipe.objects.all().select_related(
            'author'
        ).prefetch_related(
            'tags', 'ingredients__ingredient'
        )

        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )

        if is_favorited == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(favorites__user=self.request.user)

        if is_in_shopping_cart == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(shopping_cart__user=self.request.user)

        return queryset

    def _get_full_recipe_response(self, recipe, status_code):
        """
        Формирует ответ с полными данными рецепта.
        """
        output_serializer = RecipeListSerializer(
            recipe,
            context={'request': self.request}
        )
        return Response(output_serializer.data, status=status_code)

    def perform_create(self, serializer):
        """Сохраняет рецепт у автора."""
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """
        Сохраняет обновленный рецепт с проверкой прав.
        """
        serializer.save()

    def perform_destroy(self, instance):
        """
        Удаляет рецепт с проверкой прав.
        """
        instance.delete()

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

    def destroy(self, request, *args, **kwargs):
        """
        Удаляет рецепт с проверкой прав.
        """
        instance = self.get_object()
        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _add_or_remove_relation(
            self, request, pk, model, error_add, error_remove
    ):
        """
        Добавляет или удаляет связь между пользователем и рецептом.

        Используется для:
        - избранного (Favorite)
        - списка покупок (ShoppingCart)
        """
        recipe = self.get_object()
        if request.method == 'POST':
            if model.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': error_add},
                    status=status.HTTP_400_BAD_REQUEST
                )

            model.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(
                recipe,
                context={'request': request}
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        relation = model.objects.filter(user=request.user, recipe=recipe)
        if not relation.exists():
            return Response(
                {'errors': error_remove},
                status=status.HTTP_400_BAD_REQUEST
            )
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавляет или удаляет рецепт из избранного."""
        return self._add_or_remove_relation(
            request, pk, Favorite,
            'Рецепт уже в избранном',
            'Рецепта нет в избранном'
        )

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Добавляет или удаляет рецепт из списка покупок."""
        return self._add_or_remove_relation(
            request, pk, ShoppingCart,
            'Рецепт уже в списке покупок',
            'Рецепта нет в списке покупок'
        )

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Скачивает список покупок.

        Поддерживаемые форматы:
        - txt (по умолчанию)
        - csv

        Суммирует ингредиенты из всех рецептов в корзине пользователя.
        Возвращает файл с чекбоксами для удобства использования.
        """
        shopping_cart = ShoppingCart.objects.filter(user=request.user)

        if not shopping_cart.exists():
            return Response(
                {'errors': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients_dict = self._collect_ingredients(shopping_cart)

        file_format = request.query_params.get('format', 'txt').lower()

        if file_format == 'csv':
            return self._generate_csv(ingredients_dict)
        else:
            return self._generate_txt(ingredients_dict)

    def _collect_ingredients(self, shopping_cart):
        """
        Собирает и суммирует ингредиенты из корзины.
        """
        ingredients_dict = {}

        for cart_item in shopping_cart:
            recipe = cart_item.recipe
            for ingredient_in_recipe in recipe.ingredients.select_related(
                'ingredient'
            ).all():
                name = ingredient_in_recipe.ingredient.name
                unit = ingredient_in_recipe.ingredient.measurement_unit
                amount = ingredient_in_recipe.amount

                key = f'{name}_{unit}'
                if key in ingredients_dict:
                    ingredients_dict[key]['amount'] += amount
                else:
                    ingredients_dict[key] = {
                        'name': name,
                        'amount': amount,
                        'unit': unit
                    }

        return ingredients_dict

    def _generate_txt(self, ingredients_dict):
        """Генерирует TXT файл с чекбоксами."""
        content_lines = ['Список покупок:\n']
        for item in ingredients_dict.values():
            content_lines.append(
                f'☐ {item["name"]} — {item["amount"]} {item["unit"]}'
            )
        content = '\n'.join(content_lines)

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def _generate_csv(self, ingredients_dict):
        """Генерирует CSV файл."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])

        for item in ingredients_dict.values():
            writer.writerow([item['name'], item['amount'], item['unit']])

        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Генерирует и возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()

        if not recipe.short_link:
            while True:
                code = generate_short_code()
                if not Recipe.objects.filter(short_link=code).exists():
                    recipe.short_link = code
                    recipe.save()
                    break

        domain = request.build_absolute_uri('/')[:-1]
        short_url = f'{domain}/s/{recipe.short_link}'

        return Response({'short-link': short_url})


def redirect_to_recipe(request, code):
    """Редирект по короткой ссылке на страницу рецепта."""
    try:
        recipe = get_object_or_404(Recipe, short_link=code)

        return redirect(f'/recipes/{recipe.id}/')
    except Http404:
        return redirect('/')
