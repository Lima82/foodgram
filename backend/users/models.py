from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from api.constants import (
    EMAIL_MAX_LENGTH,
    ROLE_ADMIN,
    ROLE_AUTHENTICATED_USER,
    ROLE_MAX_LENGTH,
    USER_FIRST_NAME_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH,
    USERNAME_REGEX,
)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя с email для логина."""

    class UserRole(models.TextChoices):
        """Класс ролей пользователя."""

        AUTH_USER = (
            ROLE_AUTHENTICATED_USER,
            'Аутентифицированный пользователь'
        )
        ADMIN = ROLE_ADMIN, 'Администратор'

    username_validator = RegexValidator(
        regex=USERNAME_REGEX,
        message='Имя пользователя содержит недопустимые символы'
    )
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[username_validator],
        verbose_name='Имя пользователя',
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.'
        }
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        db_index=True,
        verbose_name='Адрес электронной почты',
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
        }
    )
    first_name = models.CharField(
        max_length=USER_FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=USER_LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    role = models.CharField(
        max_length=ROLE_MAX_LENGTH,
        choices=UserRole.choices,
        default=UserRole.AUTH_USER,
        verbose_name='Роль'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username

    def clean(self):
        """Запрет на 'me' в username"""
        super().clean()
        if self.username and self.username.lower() == 'me':
            raise ValidationError({
                'username': 'Имя пользователя "me" запрещено.'
            })

    @property
    def is_admin(self):
        """Проверка, является ли пользователь администратором."""
        return self.role == self.UserRole.ADMIN or self.is_superuser


class Subscription(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
