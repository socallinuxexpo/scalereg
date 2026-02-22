from django.urls import path

from reg23.scanner import views

urlpatterns = [
    path('', views.index),
]
