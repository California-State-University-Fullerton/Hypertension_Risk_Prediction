from django.urls import path
from . import views


urlpatterns = [
    path('', views.Login, name='Login'),
    path('process', views.Process, name='Process'),
    path('main', views.Main, name='Index'),
]
