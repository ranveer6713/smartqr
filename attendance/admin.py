"""
Attendance app admin configuration.
"""

from django.contrib import admin
from .models import Subject, AttendanceSession, Attendance


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'semester']
    search_fields = ['code', 'name', 'department']
    list_filter = ['department', 'semester']


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = [
        'subject_name', 'faculty', 'branch', 'semester',
        'section', 'status', 'start_time', 'expiry_time', 'total_present'
    ]
    list_filter = ['status', 'branch', 'semester']
    search_fields = ['subject_name', 'faculty__username', 'branch']
    readonly_fields = ['session_id', 'token', 'start_time', 'qr_code']
    ordering = ['-start_time']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'roll_number', 'full_name', 'department',
        'semester', 'section', 'ip_address', 'marked_at'
    ]
    list_filter = ['department', 'semester', 'session']
    search_fields = ['roll_number', 'full_name']
    readonly_fields = ['marked_at', 'ip_address']
