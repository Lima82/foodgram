from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

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

    list_display = ('id', 'name', 'slug')  # добавлено id
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class IngredientAdmin(admin.ModelAdmin):
    """Настройки админки  для игредиентов."""

    list_display = ('id', 'name', 'measurement_unit')  # добавлено id
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
        'get_tags',  # добавлено показываем теги
        # 'image',  # убрано
        'get_image_preview',  # добавлено показываем миниатюру
        # 'text',  # убрано
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
        ).prefetch_related('tags')  # добавлено для оптимизации запроса тегов

    @admin.display(description='В избранном', ordering='favorite_count')
    def favorite_count(self, obj):
        """Подсчет, сколько раз рецепт был добавлен в избранное."""
        return obj.favorite_count

    # добавляем 
    @admin.display(description='Теги')
    def get_tags(self, obj):
        """Показывает теги в виде строки."""
        return ", ".join([tag.name for tag in obj.tags.all()])

    @admin.display(description='Изображение')
    def get_image_preview(self, obj):
        """Показывает миниатюру изображения."""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50">',
                obj.image.url
            )
        return "-"


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
