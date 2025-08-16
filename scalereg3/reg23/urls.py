from django.urls import path

from . import views

urlpatterns = [
    # Registration
    path('', views.index),
    path('add_items/', views.add_items),
    path('add_attendee/', views.add_attendee),
    path('registered_attendee/', views.registered_attendee),
    path('start_payment/', views.start_payment),
]
