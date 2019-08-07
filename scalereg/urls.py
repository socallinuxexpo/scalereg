"""scalereg URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as django_auth_views
from django.views.generic import RedirectView
from scalereg.auth_helper import views as auth_helper_views


urlpatterns = [
    url(r'^accounts/$', auth_helper_views.index),
    url(r'^accounts/profile/$', auth_helper_views.profile),
    url(r'^accounts/login/$', django_auth_views.login,
       {'template_name': 'admin/login.html'}),
    url(r'^accounts/logout/$', django_auth_views.logout),
    url(r'^accounts/password_change/$',
       django_auth_views.password_change),
    url(r'^accounts/password_change/done/$',
       django_auth_views.password_change_done),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^reg6/', include('scalereg.reg6.urls')),
    url(r'^reports/', include('scalereg.reports.urls')),
    url(r'^sponsorship/', include('scalereg.sponsorship.urls')),

    # redirect index page to reg6, since that is likely what the user wants.
    url(r'^$',
        RedirectView.as_view(url='https://register.socallinuxexpo.org/reg6/',
                             permanent=False)),
]

handler500 = 'scalereg.common.views.handler500'
