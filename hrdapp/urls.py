from django.urls import path
from . import views


urlpatterns = [
    path('', views.Main, name='Login'),
    path('process', views.Process, name='Process'),
]
