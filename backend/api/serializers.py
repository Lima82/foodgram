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
from users.models import Subscription, User
from users.serializers import UserSerializer


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
        return UserSerializer(obj.author, context=self.context).data

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное текущим пользователем."""
        request = self.context.get('request')

        return (
            bool(request)
            and request.user.is_authenticated
            and obj.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """
        Проверяет, добавлен ли рецепт в список покупок текущим пользователем.
        """
        request = self.context.get('request')

        return (
            bool(request)
            and request.user.is_authenticated
            and obj.shopping_cart.filter(user=request.user).exists()
        )

    def get_image(self, obj):
        """Возвращает URL изображения или None."""
        if obj.image and obj.image.url:
            return obj.image.url

        return ''


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = RecipeComposition
        fields = ('id', 'amount')


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

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients', 'name', 'image', 'text',
            'cooking_time',
        )

    def validate(self, data):
        """Общая валидация для создания и обновления рецепта."""
        instance = getattr(self, 'instance', None)

        tags = data.get('tags')
        if tags is not None:
            if not tags:
                raise serializers.ValidationError(
                    {'tags': 'Нужно указать хотя бы один тег'}
                )
            tag_ids = [tag.id for tag in tags]
            if len(tag_ids) != len(set(tag_ids)):
                raise serializers.ValidationError(
                    {'tags': 'Теги не должны повторяться'}
                )

        ingredients = data.get('ingredients')
        if ingredients is not None:
            if not ingredients:
                raise serializers.ValidationError(
                    {'ingredients': 'Добавьте ингредиенты'}
                )
            ingredient_ids = [item['ingredient'].id for item in ingredients]
            if len(ingredient_ids) != len(set(ingredient_ids)):
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты не должны повторяться'}
                )

        if instance is not None:
            if 'tags' not in self.initial_data:
                raise serializers.ValidationError(
                    {'tags': 'Это поле обязательно для обновления рецепта.'}
                )
            if 'ingredients' not in self.initial_data:
                raise serializers.ValidationError({
                    'ingredients': (
                        'Это поле обязательно для обновления рецепта.'
                    )
                })

        return data

    def _create_ingredients(self, recipe, ingredients):
        """Создает ингредиенты для рецепта."""
        recipe_ingredients = [
            RecipeComposition(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients
        ]
        RecipeComposition.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        """Создает рецепт с тегами и ингредиентами."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        self._create_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        instance = super().update(instance, validated_data)
        instance.tags.set(tags)

        # ingredients, в данном случае, это обратная связь через
        # RecipeComposition, null=False по умолчанию, поэтому .clear()
        # не доступен. Если поставить null=True, то можем получить в таблице
        # recipes_recipecomposition ингредиенты и их количество без привязки
        # к рецепту, поэтому я использую .all().delete()
        instance.ingredients.all().delete()
        self._create_ingredients(instance, ingredients)

        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        read_only_fields = ('user', 'recipe')

    def validate(self, data):
        """Проверяет, что рецепт еще не в избранном."""
        request = self.context.get('request')
        recipe = self.context.get('recipe')
        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном')
        return data

    def create(self, validated_data):
        """Создает запись в избранном."""
        request = self.context.get('request')
        recipe = self.context.get('recipe')
        return Favorite.objects.create(user=request.user, recipe=recipe)

    def to_representation(self, instance):
        """Форматирует ответ."""
        return ShortRecipeSerializer(
            instance.recipe, context=self.context
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        read_only_fields = ('user', 'recipe')

    def validate(self, data):
        """Проверяет, что рецепт еще не в списке покупок."""
        request = self.context.get('request')
        recipe = self.context.get('recipe')
        if ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            raise serializers.ValidationError('Рецепт уже в списке покупок')
        return data

    def create(self, validated_data):
        """Создает запись в списке покупок."""
        request = self.context.get('request')
        recipe = self.context.get('recipe')
        return ShoppingCart.objects.create(user=request.user, recipe=recipe)

    def to_representation(self, instance):
        """Форматирует ответ."""
        return ShortRecipeSerializer(
            instance.recipe, context=self.context
        ).data


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
        model = User
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
                if limit > 0:
                    recipes = recipes[:limit]
            except ValueError:
                pass

        return ShortRecipeSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_avatar(self, obj):
        """Возвращает URL аватара или None."""
        if obj.author.avatar:
            return obj.author.avatar.url
        return None


class SubscribeCreateSerializer(serializers.Serializer):
    """Сериализатор для создания подписки."""
    author_id = serializers.IntegerField()

    def validate_author_id(self, value):
        """Проверяет, что пользователь не подписывается на себя."""
        request = self.context.get('request')
        user = request.user

        if user.id == value:
            raise serializers.ValidationError('Нельзя подписаться на себя')

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('Пользователь не найден')

        if Subscription.objects.filter(user=user, author_id=value).exists():
            raise serializers.ValidationError('Вы уже подписаны')

        return value

    def create(self, validated_data):
        """Создает подписку."""
        request = self.context.get('request')
        subscription = Subscription.objects.create(
            user=request.user,
            author_id=validated_data['author_id']
        )
        return subscription

    def to_representation(self, instance):
        """Форматирует ответ для создания подписки."""
        return SubscriptionSerializer(instance, context=self.context).data


class AvatarSerializer(serializers.Serializer):
    """Сериализатор для загрузки аватара."""
    avatar = Base64ImageField()
