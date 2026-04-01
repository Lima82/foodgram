import django_filters

from recipes.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    """
    Фильтр для рецептов.

    Позволяет фильтровать по:
    - тегам (tags)
    - автору (author)
    - избранному (is_favorited)
    - списку покупок (is_in_shopping_cart)
    """

    # tags = django_filters.CharFilter(
    #     field_name='tags__slug',
    #     lookup_expr='exact',
    #     method='filter_tags',
    # )
    # tags = django_filters.BaseInFilter(
    #     field_name='tags__slug',
    #     lookup_expr='in',
    #     method='filter_tags'
    # )
    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        method='filter_tags'
    )
    author = django_filters.NumberFilter(
        field_name='author__id',
    )
    is_favorited = django_filters.BooleanFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author']

    def filter_tags(self, queryset, name, value):
        """
        Фильтрация по нескольким тегам.
        value может быть строкой с тегами через запятую или списком.
        """
        # if isinstance(value, str):
        #     tags = value.split(',')
        # else:
        #     # tags = [value]
        #     tags = value

        # return queryset.filter(tags__slug__in=tags).distinct()
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
