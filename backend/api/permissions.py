from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Кастомное разрешение для рецептов:

    - Читать могут все
    - Создавать рецепт может любой авторизованный пользователь
    - Редактировать/удалять может только автор рецепта
    - Дополнительные действия (favorite, shopping_cart, get_short_link,
    download_shopping_cart) требуют аутентификации.
    """

    def has_permission(self, request, view):
        """
        Проверка на уровне запроса (без объекта).
        """
        if request.method == 'POST':
            return request.user.is_authenticated

        return True

    def has_object_permission(self, request, view, obj):
        """
        Проверка на уровне объекта.
        """
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
