"""
Accounts app models.

We extend Django's built-in User model with a Faculty profile that stores
additional college-specific information.
"""

from django.db import models
from django.contrib.auth.models import User


class FacultyProfile(models.Model):
    """
    One-to-one extension of the Django User model.
    Stores college-specific faculty information.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='faculty_profile'
    )
    department = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(
        upload_to='faculty/profiles/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Faculty Profile'
        verbose_name_plural = 'Faculty Profiles'

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
