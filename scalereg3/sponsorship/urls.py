from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('add_items/', views.add_items),
]
