"""
Root URL configuration for Smart QR Attendance System.
Routes traffic to individual app URL modules.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts app — login, logout, password change
    path('accounts/', include('accounts.urls')),

    # Dashboard — faculty home
    path('dashboard/', include('dashboard.urls')),

    # Attendance — session creation, QR display, student form
    path('attendance/', include('attendance.urls')),

    # Reports — historical sessions, CSV/Excel export
    path('reports/', include('reports.urls')),

    # Redirect root URL → dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
]

# Serve media files during development (QR code images)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
