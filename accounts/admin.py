"""
Accounts app admin registration.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import FacultyProfile


class FacultyProfileInline(admin.StackedInline):
    """Inline faculty profile in User admin."""
    model = FacultyProfile
    can_delete = False
    verbose_name_plural = 'Faculty Profile'


class CustomUserAdmin(UserAdmin):
    """Extend User admin to include FacultyProfile inline."""
    inlines = (FacultyProfileInline,)


# Re-register User with the custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(FacultyProfile)
