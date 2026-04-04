from djoser import serializers as djoser_serializers
from rest_framework import serializers

from users.models import User, Subscription


# В стандартном UserCreateSerializer Djoser нет полей first_name и last_name
# Без этого класса тесты Postman сразу падают с ошибкой
class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    """Сериализатор для регистрации."""

    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'password'
        )


class UserSerializer(djoser_serializers.UserSerializer):
    """Сериализатор для просмотра пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta(djoser_serializers.UserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на другого."""
        request = self.context.get('request')

        return (
            bool(request)
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        )
