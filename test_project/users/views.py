# -*- coding:utf-8 -*-
from django import http
from django.contrib import messages, auth
from django.shortcuts import redirect, render_to_response
from django.core.urlresolvers import reverse
from django.template.context import RequestContext

from .forms import CompleteReg

from loginza import signals, models
from loginza.templatetags.loginza_widget import _return_path


def loginza_error_handler(sender, error, **kwargs):
    messages.error(sender, error.message)

signals.error.connect(loginza_error_handler)

def loginza_auth_handler(sender, user, identity, **kwargs):
    try:
        # it's enough to have single identity verified to treat user as verified
        models.UserMap.objects.get(user=user, verified=True)
        auth.login(sender, user)
    except models.UserMap.DoesNotExist:
        sender.session['users_complete_reg_id'] = identity.id
        return redirect(reverse('users.views.complete_registration'))

signals.authenticated.connect(loginza_auth_handler)

def loginza_login_required(sender, **kwargs):
    messages.warning(sender, u'Функция доступна только авторизованным пользователям.')

signals.login_required.connect(loginza_login_required)


def complete_registration(request):
    if request.user.is_authenticated():
        return http.HttpResponseForbidden(u'Вы попали сюда по ошибке')
    try:
        identity_id = request.session.get('users_complete_reg_id', None)
        user_map = models.UserMap.objects.get(identity__id=identity_id)
    except models.UserMap.DoesNotExist:
        return http.HttpResponseForbidden(u'Вы попали сюда по ошибке')
    if request.method == 'POST':
        form = CompleteReg(user_map.user.id, request.POST)
        if form.is_valid():
            user_map.user.username = form.cleaned_data['username']
            user_map.user.email = form.cleaned_data['email']
            user_map.user.save()

            user_map.verified = True
            user_map.save()

            user = auth.authenticate(user_map=user_map)
            auth.login(request, user)

            messages.info(request, u'Добро пожаловать!')
            del request.session['users_complete_reg_id']
            return redirect(_return_path(request))
    else:
        form = CompleteReg(user_map.user.id, initial={
            'username': user_map.user.username, 'email': user_map.user.email,
            })

    return render_to_response('users/complete_reg.html',
                              {'form': form},
                              context_instance=RequestContext(request),
                              )