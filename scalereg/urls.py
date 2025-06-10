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
from django.urls import include, re_path
from django.contrib import admin
from django.contrib.auth import views as django_auth_views
from django.views.generic import RedirectView
from scalereg.auth_helper import views as auth_helper_views


urlpatterns = [
    re_path(r'^accounts/$', auth_helper_views.index),
    re_path(r'^accounts/profile/$', auth_helper_views.profile),
    re_path(r'^accounts/login/$', django_auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    re_path(r'^accounts/logout/$', django_auth_views.LogoutView.as_view(), name='logout'),
    re_path(r'^accounts/password_change/$',
       django_auth_views.PasswordChangeView.as_view(), name='password_change'),
    re_path(r'^accounts/password_change/done/$',
       django_auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^reg6/', include('scalereg.reg6.urls')),
    re_path(r'^reports/', include('scalereg.reports.urls')),
    re_path(r'^sponsorship/', include('scalereg.sponsorship.urls')),

    # redirect index page to reg6, since that is likely what the user wants.
    re_path(r'^$',
        RedirectView.as_view(url='https://register.socallinuxexpo.org/reg6/',
                             permanent=False)),
]

handler500 = 'scalereg.common.views.handler500'
