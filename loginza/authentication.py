# -*- coding:utf-8 -*-
try:
    from django.contrib.auth import get_user_model
except ImportError: # django < 1.5
    from django.contrib.auth.models import User
else:
    User = get_user_model()

class LoginzaBackend(object):
    supports_object_permissions = False
    supports_anonymous_user = False

    def authenticate(self, user_map=None):
        return user_map.user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class LoginzaError(object):
    type = None
    message = None

    def __init__(self, data):
        self.type = data['error_type']
        self.message = data['error_message']
