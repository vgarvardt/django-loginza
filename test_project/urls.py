from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

admin.autodiscover()


urlpatterns = patterns('',
	url(r'^admin/', include(admin.site.urls)),

    url(r'^$', TemplateView.as_view(template_name='base.html')),

    url(r'^loginza/', include('loginza.urls')),
    url(r'^users/', include('users.urls')),  
)
