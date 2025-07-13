from django.urls import path

from . import views

urlpatterns = [
    # Registration
    path('', views.index),
    path('add_items/', views.add_items),
]
