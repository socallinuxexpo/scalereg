from django.conf.urls import *
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/$', 'scalereg.auth_helper.views.index'),
    (r'^accounts/profile/$', 'scalereg.auth_helper.views.profile'),
    (r'^accounts/login/$', 'django.contrib.auth.views.login',
     {'template_name': 'admin/login.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^accounts/password_change/$',
     'django.contrib.auth.views.password_change'),
    (r'^accounts/password_change/done/$',
     'django.contrib.auth.views.password_change_done'),
    (r'^admin/', include(admin.site.urls)),
    (r'^reg6/', include('scalereg.reg6.urls')),
    (r'^reports/', include('scalereg.reports.urls')),
    (r'^simple_cfp/', include('scalereg.simple_cfp.urls')),
    (r'^speaker_survey/', include('scalereg.speaker_survey.urls')),

    # dummy index page
    (r'^$', 'scalereg.auth_helper.views.index'),

)

handler500 = 'scalereg.common.views.handler500'
