from django.contrib import admin
from django.db.models import Count

from recipes.models import (
    Ingredient,
    Favorite,
    Recipe,
    RecipeComposition,
    ShoppingCart,
    Tag,
)


class TagAdmin(admin.ModelAdmin):
    """Настройки админки  для тегов."""

    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class IngredientAdmin(admin.ModelAdmin):
    """Настройки админки  для игредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeCompositionInline(admin.TabularInline):
    """Настройки админки для ингредиентов в рецепте."""

    model = RecipeComposition
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    """Настройки админки для рецептов."""

    list_display = (
        'id',
        'name',
        'author',
        'image',
        'text',
        'favorite_count',
        'cooking_time',
        'pub_date'
    )
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'author')
    inlines = [RecipeCompositionInline]
    readonly_fields = ('favorite_count',)

    def get_queryset(self, request):
        """Подсчет количества рецептов в избранном."""
        return super().get_queryset(request).annotate(
            favorite_count=Count('favorites', distinct=True)
        )

    @admin.display(description='В избранном', ordering='favorite_count')
    def favorite_count(self, obj):
        """Подсчет, сколько раз рецепт был добавлен в избранное."""
        return obj.favorite_count


class FavoriteAdmin(admin.ModelAdmin):
    """Настройка админки для избранного."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройка админки для листа покупок."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
