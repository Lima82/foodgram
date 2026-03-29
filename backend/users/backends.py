from django.contrib.auth.backends import ModelBackend

from users.models import CustomUser


class EmailAuthBackend(ModelBackend):
    """Аутентификация по email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(email=username)
        except CustomUser.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None
