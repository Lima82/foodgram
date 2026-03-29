from djoser import serializers as djoser_serializers
from rest_framework import serializers

from api.fields import Base64ImageField
from users.models import CustomUser, Subscription


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    """Сериализатор для регистрации."""

    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'password'
        )


class CustomUserSerializer(djoser_serializers.UserSerializer):
    """Сериализатор для просмотра пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta(djoser_serializers.UserSerializer.Meta):
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на другого."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False


class AvatarSerializer(serializers.Serializer):
    """Сериализатор для загрузки аватара."""
    avatar = Base64ImageField()
