from django.db.models import BooleanField, Case, Value, When
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для рецептов.

    Позволяет фильтровать по:
    - тегам (tags)
    - автору (author)
    - избранному (is_favorited)
    - списку покупок (is_in_shopping_cart)
    """

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        method='filter_tags'
    )
    author = filters.NumberFilter(
        field_name='author__id',
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        """
        Фильтрация по нескольким тегам.
        """
        if value:
            return queryset.filter(tags__slug__in=value).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация по избранному (только для авторизованных)."""
        if value and self.request and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)

        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по списку покупок (только для авторизованных)."""
        if value and self.request and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)

        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов с поиском по названию."""

    name = filters.CharFilter(method='filter_by_name')

    def filter_by_name(self, queryset, name, value):
        """
        Фильтрует ингредиенты по параметру name.
        Для одного символа - только начинающиеся с этого символа.
        Для двух и более - поиск по вхождению с сортировкой.
        """
        if not value:
            return queryset

        if len(value) == 1:
            return queryset.filter(name__istartswith=value)

        queryset = queryset.annotate(
            starts_with=Case(
                When(name__istartswith=value, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        return queryset.filter(
            name__icontains=value
        ).order_by('-starts_with', 'name')

    class Meta:
        model = Ingredient
        fields = ('name',)
