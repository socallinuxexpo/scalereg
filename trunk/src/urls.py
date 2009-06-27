from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    # (r'^scale/', include('scale.apps.foo.urls.foo')),

    (r'^accounts/$', 'scale.auth_helper.views.index'),
    (r'^accounts/profile/$', 'scale.auth_helper.views.profile'),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^accounts/password_change/$', 'django.contrib.auth.views.password_change'),
    (r'^accounts/password_change/done/$', 'django.contrib.auth.views.password_change_done'),
    (r'^admin/(.*)', admin.site.root),
    (r'^reg6/', include('scale.reg6.urls')),
    (r'^reports/', include('scale.reports.urls')),
    (r'^speaker_survey/', include('scale.speaker_survey.urls')),

    # dummy index page
    (r'^$', 'scale.auth_helper.views.index'),

)
