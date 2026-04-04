import random
import string

from django.db import models
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)

from api.constants import (
    INGREDIENT_AMOUNT_MAX,
    INGREDIENT_AMOUNT_MIN,
    INGREDIENT_NAME_MAX_LENGTH,
    COOKING_TIME_MAX,
    COOKING_TIME_MIN,
    MEASUREMENT_UNIT_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
    SLUG_MAX_LENGTH,
    SLUG_REGEX,
    SHORT_CODE_FOR_LINK,
    SHORT_LINK_MAX_LENGTH,
    TAG_MAX_LENGTH
)
from users.models import User


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        max_length=TAG_MAX_LENGTH,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        validators=[RegexValidator(
            regex=SLUG_REGEX,
            message='Слаг тега содержит недопустимые символы'
        )],
        verbose_name='Уникальный слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение'
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                COOKING_TIME_MIN,
                message='Время приготовления не может быть меньше 1 минуты'
            ),
            MaxValueValidator(
                COOKING_TIME_MAX,
                message='Время приготовления не может быть больше 32000 минут'
            ),
        ],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    short_link = models.CharField(
        max_length=SHORT_LINK_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткая ссылка'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name

    def _generate_short_code(self, length=SHORT_CODE_FOR_LINK):
        """Генерирует случайный код для короткой ссылки."""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def save(self, *args, **kwargs):
        """Генерирует короткую ссылку при создании, если её нет."""
        if not self.short_link:
            while True:
                code = self._generate_short_code()
                if not Recipe.objects.filter(short_link=code).exists():
                    self.short_link = code
                    break
        super().save(*args, **kwargs)


class RecipeComposition(models.Model):
    """Модель определения количества ингредиента в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                INGREDIENT_AMOUNT_MIN,
                message='Количество ингредиента не может быть меньше 1'
            ),
            MaxValueValidator(
                INGREDIENT_AMOUNT_MAX,
                message='Количество ингредиента не может быть больше 32000'
            ),
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} - '
            f'{self.amount} '
            f'{self.ingredient.measurement_unit}'
        )


class Favorite(models.Model):
    """Модель для раздела 'Избранное'."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное'


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в список покупок'
