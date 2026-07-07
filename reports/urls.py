"""
Reports app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='list'),
    path('<int:pk>/', views.report_detail, name='detail'),
    path('<int:pk>/export/csv/', views.export_csv, name='export_csv'),
    path('<int:pk>/export/excel/', views.export_excel, name='export_excel'),
]
