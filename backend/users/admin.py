from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, Group
from django.db.models import Count
from django.contrib.admin.sites import NotRegistered

from users.models import CustomUser, Subscription

try:
    admin.site.unregister(Group)
except NotRegistered:
    pass


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    fk_name = 'user'
    extra = 0
    verbose_name = 'Подписки пользователя'
    verbose_name_plural = 'Подписки'


class CustomUserAdmin(UserAdmin):
    """Настройка админки юзера."""

    list_display = (
        'username', 'email', 'first_name',
        'last_name', 'avatar', 'role'
    )
    search_fields = ('username', 'email')
    list_filter = ('role',)
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar', 'role')}),
    )
    inlines = [SubscriptionInline]

    def get_queryset(self, request):
        """
        Добавляет к каждому пользователю виртуальные поля:
        - subscribers_count: количество подписчиков (кто подписан на этого
        пользователя)
        - following_count: количество подписок (на кого подписан этот
        пользователь)
        """
        return super().get_queryset(request).annotate(
            subscribers_count=Count('subscribers', distinct=True),
            following_count=Count('follower', distinct=True)
        )

    @admin.display(description='Подписчиков', ordering='subscribers_count')
    def subscribers_count(self, obj):
        """Возвращает количество подписчиков пользователя."""
        return obj.subscribers_count

    @admin.display(description='Подписан', ordering='following_count')
    def following_count(self, obj):
        """Возвращает количество подписок пользователя."""
        return obj.following_count

    @admin.action(description="Удалить выбранных пользователей")
    def delete_selected(self, request, queryset):
        """Удаление выбранных пользователей"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'Успешно удалено {count} пользователей.')

    actions = ['delete_selected']


class SubscriptionAdmin(admin.ModelAdmin):
    """Настройка админки дял подписок для модели юзера."""
    list_display = ('user', 'author', 'created_at')
    search_fields = ('user__username', 'author__username')
    list_filter = ('created_at',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
