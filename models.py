from django.contrib.auth.models import User
from django.db import models
from django.utils import simplejson as json

from loginza import signals
from loginza.conf import settings

class IdentityManager(models.Manager):
    def from_loginza_data(self, loginza_data):
        try:
            identity = self.get(identity=loginza_data['identity'])
        except self.model.DoesNotExist:
            identity = self.create(
                    identity=loginza_data['identity'],
                    provider=loginza_data['provider'],
                    data=json.dumps(loginza_data)
                    )
        return identity

class UserMapManager(models.Manager):
    def for_identity(self, identity, request):
        try:
            user_map = self.get(identity=identity)
        except self.model.DoesNotExist:
            # if there is authenticated user - map identity to that user
            # if not - create new user and mapping for him
            if request.user.is_authenticated():
                user = request.user
            else:
                loginza_data = json.loads(identity.data)
                loginza_email = loginza_data.get('email', '')
                email = loginza_email if '@' in loginza_email else settings.DEFAULT_EMAIL
                user = User.objects.create_user(
                        loginza_data['nickname'],
                        email,
                        User.objects.make_random_password()
                        )
            user_map = UserMap.objects.create(identity=identity, user=user)
            signals.created.send(request, user_map=user_map)
        return user_map

class Identity(models.Model):
    identity = models.CharField(max_length=255, unique=True)
    provider = models.CharField(max_length=255)
    data = models.TextField()

    objects = IdentityManager()

    def __unicode__(self):
        return self.identity

    class Meta:
        ordering = ['id']
        verbose_name_plural = "identities"


class UserMap(models.Model):
    identity = models.OneToOneField(Identity)
    user = models.ForeignKey(User)
    verified = models.BooleanField(default=False, db_index=True)

    objects = UserMapManager()

    def __unicode__(self):
        return '%s [%s]' % (unicode(self.user), self.identity.provider)

    class Meta:
        ordering = ['user']
