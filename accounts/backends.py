from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailOUsernameBackend(ModelBackend):
    """Permet login amb email o username."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            user = User.objects.filter(username=username).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
