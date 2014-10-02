from django.conf.urls import patterns, url

from loginza import views

urlpatterns = patterns(
    '',
    url(r'return_callback/$', views.return_callback, name='loginza_return')
)
