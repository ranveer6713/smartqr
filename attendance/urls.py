"""
Attendance app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # --- Faculty URLs (login required) ---
    path('create/', views.create_session, name='create_session'),
    path('session/<int:pk>/qr/', views.session_qr, name='session_qr'),
    path('session/<int:pk>/qr-image/', views.session_qr_image, name='session_qr_image'),
    path('session/<int:pk>/close/', views.close_session, name='close_session'),
    path('session/<int:pk>/detail/', views.session_detail, name='session_detail'),
    path(
        'session/<int:session_pk>/delete/<int:attendance_pk>/',
        views.delete_attendance,
        name='delete_attendance'
    ),

    # --- Student URLs (no login) ---
    # URL embedded in QR code: /attendance/<uuid>/<token>/
    path(
        '<uuid:session_id>/success/',
        views.attendance_success,
        name='attendance_success'
    ),
    path(
        '<uuid:session_id>/<str:token>/',
        views.mark_attendance,
        name='mark_attendance'
    ),
]
