==============
Django Loginza
==============

Django-приложение, обеспечивающее работу с сервисом авторизации Loginza (loginza.ru)

Установка
=========

Установка производится с помощью ``pip``::

 $ pip install django-loginza

Или добавлением следующей строчки в ``project_name/requirements.txt``::

 django-loginza

А затем установкой через ``pip``::

 $ pip install -r project_name/requirements.txt

Последняя актуальная версия доступна в `репозитории GitHub`__.

Для корректной работы приложения необходимо, чтобы так же был установлено приложения 
``django.contrib.auth``, ``django.contrib.sessions`` и ``django.contrib.sites``.

После этого, необходимо добавить приложение в ``INSTALLED_APPS`` и добавить бэкэнд авторизации -
``loginza.authentication.LoginzaBackend`` в ``AUTHENTICATION_BACKENDS``. В общем случае, бэкэнды
авторизации после добавления нового, будут выглядеть так::

 AUTHENTICATION_BACKENDS = (
     'django.contrib.auth.backends.ModelBackend',
     'loginza.authentication.LoginzaBackend',
 )

В этом случае, можно будет использовать как стандартную форму авторизации по логину и паролю
(например, для доступа в админскую панель), так и loginza-авторизацию.

Также, следует добавить в ``TEMPLATE_CONTEXT_PROCESSORS`` строчку 
``django.core.context_processors.request``.

После добавления приложения, необходимо установить необходимые таблицы в БД (выполнить
``python manage.py syncdb`` в корне проекта).

Далее, нужно зарегистрировать ссылки приложения в проекте. В общем случае,
необходимо добавить следующий элемент в ``urlpatterns`` проекта в ``urls.py``::

 (r'^loginza/', include('loginza.urls')),

Чтобы при авторизации через loginza вас не перенаправляло не пойми куда (например, example.com) -
следует в админке, в настройках сайтов указать правильный домен.


Использование
=============

Приложение можно условно разделить на три составляющих:

- шаблонные теги, для отображения виджета авторизации на странице
- сигналы, позволяющие другим приложениям взаимодействовать с данным
- внутренняя логика приложения

Этот документ рассматривает только первые две составляющие.

Шаблонные теги
==============

Для того, чтобы отобразить виджет авторизации в шаблоне, сначала необходимо загрузить тэги::

 {% load loginza_widget %}

После этого, становятся доступны следующие теги:

- ``loginza_iframe`` - встраиваемый виджета авторизации Loginza (спаренная форма авторизации)
- ``loginza_button`` - кнопка виджета Loginza
- ``loginza_icons`` - набор иконок провайдеров
- ``loginza_string`` - строка (ссылка)

Примеры отображения виджетов можно посмотреть на странице
`Примеры интеграции Loginza в форму авторизации сайта`__.

Для всех тэгов, кроме ``loginza_iframe`` необходим обязательный параметр caption.
Для ``loginza_button`` он используется для атрибутов ``alt`` и ``title`` изображения кнопки,
для ``loginza_icons`` - текст, перед набором иконок (например, *Войти используя:*),
для ``loginza_string`` - собственно сама строка.

Так же, для всех виджетов доступны следующие именованные параметры:

- ``lang`` - язык виджета
- ``providers_set`` - доступные кнопки и порядок провайдеров
- ``provider`` - провайдер авторизации по умолчанию

Например::

  {% loginza_iframe providers_set="google,facebook,twitter" lang="en" %}

Более подробно об этих параметрах можно прочитать в `Руководстве по Loginza.API`__.

Дополнительно, для ``loginza_iframe`` доступны параметры ``width`` и ``height``,
которыми можно задать размер виджета (по умолчанию 359 x 300 px).

В общем случае шаблон, отвечающий за авторизацию, будет выглядеть следующим образом::

 {% load loginza_widget %}
 {% if user.is_authenticated %}
   Добро пожаловать, {{ user }}
 {% else %}
   {% loginza_button "Войти через Loginza" %}
 {% endif %}

Сигналы
=======

Приложение предоставляет следующие сигналы:

- ``created`` - создана новая связка между идентификатором Loginza и пользователем Django
- ``error`` - во время авторизации произошла ошибка
- ``authenticated`` - пользователь успешно авторизован (authenticated) и готов быть залогинен
- ``login_required`` - декоратор login_required обнаружил, что пользователь не авторизован

Более подробно о сигналах и их параметрах можно прочитать в их документации к сигналам в ``signals.py``
приложения.

Пример ``views.py`` вспомогательного приложения ``users``, использующего сигналы приложения ``loginza``::

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

Пример ``forms.py`` вспомогательного приложения ``users``::

  # -*- coding:utf-8 -*-
  from django import forms
  from django.contrib.auth.models import User


  class CompleteReg(forms.Form):

      username = forms.RegexField(label=u'Имя пользователя', max_length=30, min_length=4, 
                                  required=True, regex=r'^[\w.@+-]+$') 
      email = forms.EmailField(label=u'Email', required=True) 


      def __init__(self, user_id, *args, **kwargs):
          super(CompleteReg, self).__init__(*args, **kwargs)
          self.user_id = user_id

      def clean_username(self):
          if self.cleaned_data['username']:
              try: u = User.objects.exclude(id=self.user_id).get(username=self.cleaned_data['username'])
              # if username is unique - it's ok
              except User.DoesNotExist: u = None

              if u is not None:
                  raise forms.ValidationError(u'Пользователь с таким именем уже зарегистрирован')
          return self.cleaned_data['username']

      def clean_email(self):
          if self.cleaned_data['email']:
              try: u = User.objects.exclude(id=self.user_id).get(email=self.cleaned_data['email'])
              # if email is unique - it's ok
              except User.DoesNotExist: u = None

              if u is not None:
                  raise forms.ValidationError(u'Пользователь с этим адресом уже зарегистрирован')
          return self.cleaned_data['email']

Пример ``urls.py`` вспомогательного приложения ``users``::

  from django.conf.urls.defaults import *

  from .views import complete_registration


  urlpatterns = patterns('',
      url(r'^complete_registration/$', complete_registration, name='users_complete_registration'),
      url(r'^logout/$', 'django.contrib.auth.views.logout', name='users_logout'),
  )


Для того, чтобы пример выше работал корректно, необходимо так же в ``settings.py`` проекта добавить
следующие настройки (подробнее читайте в разделе *Настройки*)::

 # can't use reverse url resolver here (raises ImportError),
 # so we should carefully control paths
 LOGINZA_AMNESIA_PATHS = ('/users/complete_registration/',)

Так же добавить приложение ``users`` в ``INSTALLED_APPS``, а затем в ``urls.py`` проекта 
добавить следующее::

 url(r'^users/', include('users.urls')),

Настройки
=========

В приложении доступны следующие настройки:

- ``LOGINZA_DEFAULT_LANGUAGE`` - язык по умолчанию, если параметр ``lang`` не задан для виджета явно.
  Выбирается на основе ``LANGUAGE_CODE`` проекта.
- ``LOGINZA_DEFAULT_PROVIDERS_SET`` - набор провайдеров, используемых по умолчанию,
  если параметр ``providers_set`` не задан. Формат - имена провайдеров через запятую,
  например 'facebook,twitter,google'. ``None`` - все доступные провайдеры.
- ``LOGINZA_DEFAULT_PROVIDER`` - провайдер, используемый по умолчанию,
  если параметр ``provider`` не задан для виджета явно. ``None`` - не задан.
- ``LOGINZA_ICONS_PROVIDERS`` - иконки провайдеров, отображаемые виджетом loginza_icons,
  по умолчанию все доступные. Используется, только если параметр `providers_set`` не задан для виджета явно и
  настройка ``LOGINZA_DEFAULT_PROVIDERS_SET`` не задана. Формат - имена провайдеров через запятую,
  например 'facebook,twitter,google'.
- ``LOGINZA_PROVIDER_TITLES`` - заголовки провайдеров, используемые для изображений виджета
  ``loginza_icons``. Формат - словарь с ключами именами провайдеров, и значениями - заголовками, например
  {'google': u'Корпорация добра', 'twitter': u'Щебетальня', 'vkontakte': u'Вконтактик'}
- ``LOGINZA_DEFAULT_EMAIL`` - адрес электронной почты, используемый для новых пользователей, в случае,
  если Loginza не предоставила, таковой. По умолчанию - 'user@loginza'. В случае, когда в данных отсутствует
  имя пользователя, идентификатор (слева от @) адреса электронной почты используется в качестве
  имени пользователя по умолчанию.
- ``LOGINZA_AMNESIA_PATHS`` - список или кортеж путей, которые не будут запоминаться для возврата.
  Например, как показано в примере выше, страница завершения регистрации не запоминается, для того,
  чтобы после успешной авторизации пользователь был возвращен на страницу, с которой авторизация началась,
  а не на пустую страницу завершения регистрации.
- ``LOGINZA_BUTTON_IMG_URL`` - ссылка на изображение, используемое для виджета Кнопка. По умолчанию
  изображение загружается с сайта loginza.ru.
- ``LOGINZA_ICONS_IMG_URLS`` - словарь со ссылками на иконки провайдеров авторизации, используемых для
  виджета Иконки. По умолчанию изображения загружаются с сайта loginza.ru.
- ``LOGINZA_IFRAME_WIDTH`` - ширина встраевомого виджета авторизации (строка, использвется как есть,
  по умолчанию 359px).
- ``LOGINZA_IFRAME_HEIGHT`` - высота встраевомого виджета авторизации (строка, использвется как есть,
  по умолчанию 300px).
- ``LOGINZA_WIDGET_ID`` - ID виджета Loginza (см. в секции `Мой виджет Loginza`__).
- ``LOGINZA_API_SIGNATURE`` - Секретный ключ виджета Loginza.

Дополнительные возможности
==========================

Приложение предоставляет модифицированный декоратор ``@login_required``. От оригинального декоратора
``django.contrib.auth.decorators.login_required`` он отличается тем, что вместо перенаправления не
авторизованных пользователей на страницу авторизации срабатывает перенаправление на предыдущую страницу.
Декоратор может быть полезен сайтам, использующим только Loginza-авторизацию и не имеющим отдельную страницу
авторизации. Так же, при срабатывании декоратора для не авторизованных пользователей, посылается сигнал
``loginza.signals.login_required``, присоединившись к которому можно, например, уведомить пользователя
о причине возврата на предыдущую страницу (как это показано в примере), и вернуть объект HttpRespose,
если необходимо выполнить действие отличное, от возвращения пользователя на предыдущую страницу.

:Автор: Владимир Гарвардт
:Благодарности: Ивану Сагалаеву, Юрию Юревичу, Денису Веселову

__ https://github.com/vgarvardt/django-loginza
__ http://loginza.ru/signin-integration
__ http://loginza.ru/api-overview
__ http://loginza.ru/my-widgets