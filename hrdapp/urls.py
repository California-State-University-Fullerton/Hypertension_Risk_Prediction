from django.urls import path
from . import views


urlpatterns = [
    path('', views.Process, name='Process'),
    path('user', views.User, name='User'),
]
