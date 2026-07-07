"""
Accounts app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.faculty_login, name='login'),
    path('register/', views.faculty_register, name='register'),
    path('logout/', views.faculty_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
]
