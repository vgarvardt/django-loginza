# -*- coding:utf-8 -*-
from urllib import urlencode
from urllib2 import urlopen
from hashlib import md5

from django import http
from django.utils import simplejson as json
from django.contrib import auth
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from loginza import models, signals
from loginza.authentication import LoginzaError
from loginza.templatetags.loginza_widget import _return_path
from loginza.conf import settings

@require_POST
@csrf_exempt
def return_callback(request):
    token = request.POST.get('token', None)
    if token is None:
        return http.HttpResponseBadRequest()

    params = {'token': token}
    if settings.WIDGET_ID is not None and settings.API_SIGNATURE is not None:
        sig = md5(token + settings.API_SIGNATURE).hexdigest()
        params.update(id=settings.WIDGET_ID, sig=sig)

    f = urlopen('http://loginza.ru/api/authinfo?%s' % urlencode(params))
    result = f.read()
    f.close()

    data = json.loads(result)

    if 'error_type' in data:
        signals.error.send(request, error=LoginzaError(data))
        return redirect(_return_path(request))

    identity = models.Identity.objects.from_loginza_data(data)
    user_map = models.UserMap.objects.for_identity(identity, request)
    response = redirect(_return_path(request))
    if request.user.is_anonymous():
        user = auth.authenticate(user_map=user_map)
        results = signals.authenticated.send(request, user=user, identity=identity)
        for callback, result in results:
            if isinstance(result, http.HttpResponse):
                response = result
                break

    return response
