from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.pagination import CustomPageNumberPagination
from api.serializers import SubscriptionSerializer
from users.models import CustomUser, Subscription
from users.serializers import AvatarSerializer, CustomUserSerializer


class CustomUserViewSet(UserViewSet):
    """ViewSet для управления пользователями."""

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        """Настраивает права доступа для разных действий."""
        if self.action in ['me', 'avatar', 'subscriptions', 'subscribe']:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        """Добавляет или удаляет аватар текущего пользователя."""
        user = request.user

        if request.method == 'PUT':
            return self._update_avatar(request, user)
        return self._delete_avatar(user)

    def _update_avatar(self, request, user):
        """Обновляет аватар пользователя."""
        serializer = AvatarSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user.avatar = serializer.validated_data['avatar']
        user.save()
        return Response({'avatar': user.avatar.url})

    def _delete_avatar(self, user):
        """Удаляет аватар пользователя."""
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        subscriptions = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, id=None):
        """Подписывает или отписывает от пользователя."""
        author = self.get_object()

        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            return self._create_subscription(request.user, author)

        return self._delete_subscription(request.user, author)

    def _create_subscription(self, user, author):
        """Создает подписку."""
        if Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Вы уже подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = Subscription.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(
            subscription, context={'request': self.request}
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_subscription(self, user, author):
        """Удаляет подписку."""
        subscription = Subscription.objects.filter(user=user, author=author)

        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
