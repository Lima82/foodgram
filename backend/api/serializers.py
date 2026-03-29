from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeComposition,
    ShoppingCart,
    Tag,
)
from users.models import Subscription
from users.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class RecipeCompositionSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeComposition
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""

    author = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeCompositionSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time',
        )

    def get_author(self, obj):
        """Возвращает информацию об авторе."""
        return CustomUserSerializer(obj.author, context=self.context).data

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное текущим пользователем."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()

        return False

    def get_is_in_shopping_cart(self, obj):
        """
        Проверяет, добавлен ли рецепт в список покупок текущим пользователем.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shopping_cart.filter(user=request.user).exists()

        return False

    def get_image(self, obj):
        """Возвращает URL изображения или None."""
        if obj.image and obj.image.url:
            return obj.image.url

        return ''


class RecipeDetailSerializer(RecipeListSerializer):
    """Сериализатор для детального просмотра рецепта."""

    pass


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """Сериализатор создания ингредиентов в рецепте."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=True,
    )
    ingredients = RecipeIngredientCreateSerializer(
        many=True,
        write_only=True,
        required=True,
    )
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients', 'name', 'image', 'text',
            'cooking_time',
        )

    def validate_tags(self, value):
        """
        Проверяет, что поле tags не пустое.
        """
        if not value:
            raise serializers.ValidationError('Нужно указать хотя бы один тег')

        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError('Теги не должны повторяться')

        return value

    def validate_ingredients(self, value):
        """Проверка валидности списка ингредиентов."""
        if not value:
            raise serializers.ValidationError('Добавьте ингредиенты')

        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )
        existing_ids = set(
            Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                'id', flat=True
            )
        )

        for item in value:
            if item['id'] not in existing_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с id {item["id"]} не найден'
                )

        return value

    def validate(self, data):
        """
        Дополнительная валидация для обновления.
        """
        instance = getattr(self, 'instance', None)

        if instance is not None:
            missing = [
                f for f in ('tags', 'ingredients')
                if f not in self.initial_data
            ]
            if missing:
                raise serializers.ValidationError({
                    f: 'Это поле обязательно для обновления рецепта.'
                    for f in missing
                })

        return data

    def create(self, validated_data):
        """Создает рецепт с тегами и ингредиентами."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for item in ingredients:
            RecipeComposition.objects.create(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.ingredients.all().delete()
            for item in ingredients:
                RecipeComposition.objects.create(
                    recipe=instance,
                    ingredient_id=item['id'],
                    amount=item['amount']
                )

        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        read_only_fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        read_only_fields = ('user', 'recipe')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Краткий сериализатор для рецептов.

    Используется для ответов при добавлении в избранное и корзину.
    Возвращает только id, name, image, cooking_time.
    """
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        """Возвращает URL изображения или None."""
        if obj.image and obj.image.url:
            return obj.image.url
        return None


class SubscriptionRecipeSerializer(ShortRecipeSerializer):
    """
    Сериализатор для рецептов в подписках.

    Наследуется от ShortRecipeSerializer.
    """

    pass


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    email = serializers.EmailField(source='author.email')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='author.recipes.count')
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Всегда возвращает True для подписки."""
        return True

    def get_recipes(self, obj):
        """Возвращает рецепты автора с учетом параметра recipes_limit."""
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.author.recipes.all()

        if limit:
            try:
                limit = int(limit)
                recipes = recipes[:limit]
            except ValueError:
                pass

        return SubscriptionRecipeSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_avatar(self, obj):
        """Возвращает URL аватара или None."""
        if obj.author.avatar:
            return obj.author.avatar.url
        return None
