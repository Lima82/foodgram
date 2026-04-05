from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.pagination import PageNumberPaginationWithLimit
from api.serializers import (
    AvatarSerializer,
    SubscribeCreateSerializer,
    SubscriptionSerializer,
    UserSerializer,
)
from users.models import Subscription, User


class UserAccountViewSet(UserViewSet):
    """ViewSet для управления пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPaginationWithLimit

    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        """
        Переопределяет метод me для ограничения доступа.

        Djoser предоставляет GET, PUT, PATCH, DELETE для /users/me/.
        Ограничивает только GET.
        """
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def update_avatar(self, request):
        """Обновляет аватар текущего пользователя."""
        user = request.user
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data['avatar']
        user.save()
        return Response({'avatar': user.avatar.url})

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар текущего пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        subscriptions = Subscription.objects.filter(user=request.user)
        authors = [sub.author for sub in subscriptions]
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписывается на пользователя."""
        author = self.get_object()
        serializer = SubscribeCreateSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отписывается от пользователя."""
        author = self.get_object()
        deleted_count, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()

        if deleted_count == 0:
            return Response(
                {'errors': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
