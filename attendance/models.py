"""
Attendance app models.

Core models:
  - Subject        : College subjects
  - AttendanceSession : A QR-code-based attendance window created by faculty
  - Attendance     : Individual student attendance record
"""

import uuid
import secrets
import os

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def qr_code_upload_path(instance, filename):
    """Dynamic upload path: media/qrcodes/<session_id>/qr.png"""
    return os.path.join('qrcodes', str(instance.session_id), filename)


class Subject(models.Model):
    """
    Represents a college subject.
    Faculty can choose a subject when creating a session.
    """
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    semester = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['name']
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'

    def __str__(self):
        return f"{self.code} — {self.name}"


class AttendanceSession(models.Model):
    """
    Represents a single QR-code attendance session created by a faculty member.

    Lifecycle:
      1. Faculty creates session → status becomes ACTIVE
      2. Timer expires OR faculty closes manually → status becomes CLOSED
    """

    # Duration choices in minutes
    DURATION_CHOICES = [
        (5,  '5 Minutes'),
        (10, '10 Minutes'),
        (15, '15 Minutes'),
        (20, '20 Minutes'),
    ]

    STATUS_ACTIVE = 'ACTIVE'
    STATUS_CLOSED = 'CLOSED'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_CHOICES = [
        (STATUS_ACTIVE,  'Active'),
        (STATUS_CLOSED,  'Closed'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    # --- Identification ---
    session_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        db_index=True
    )

    # --- Ownership ---
    faculty = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_sessions'
    )

    # --- Session details ---
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    subject_name = models.CharField(max_length=150)   # Snapshot in case Subject is deleted
    branch = models.CharField(max_length=100)
    semester = models.PositiveSmallIntegerField()
    section = models.CharField(max_length=10)
    classroom = models.CharField(max_length=50)
    duration_minutes = models.PositiveSmallIntegerField(choices=DURATION_CHOICES, default=10)
    meeting_link = models.URLField(max_length=500, blank=True, null=True)
    require_photo = models.BooleanField(default=False)

    # --- Timing ---
    start_time = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()

    # --- State ---
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True
    )

    # --- QR Code image ---
    qr_code = models.ImageField(upload_to=qr_code_upload_path, null=True, blank=True)

    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Attendance Session'
        verbose_name_plural = 'Attendance Sessions'

    def __str__(self):
        return f"{self.subject_name} | {self.faculty.get_full_name()} | {self.start_time:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        """Generate a secure random token on first save."""
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def get_student_url(self, request):
        """Build the absolute URL for students to scan/access (handles local and production/Vercel)."""
        host = request.get_host()
        parts = host.split(':')
        hostname = parts[0]
        
        # If running locally on localhost/127.0.0.1, resolve the LAN IP so other devices can connect
        if hostname == '127.0.0.1' or hostname == 'localhost':
            from .utils import get_local_ip
            local_ip = get_local_ip()
            port = parts[1] if len(parts) > 1 else '80'
            host = f"{local_ip}:{port}"
            
        protocol = 'https' if request.is_secure() or request.META.get('HTTP_X_FORWARDED_PROTO') == 'https' else 'http'
        return f"{protocol}://{host}/attendance/{self.session_id}/{self.token}/"

    def get_qr_code_base64(self, student_url):
        """Generate a base64 encoded PNG image data URI for the QR code (no disk writes)."""
        import io
        import base64
        import qrcode
        
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(student_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color='#1a1a2e', back_color='white')
        img = img.convert('RGB')
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"

    @property
    def is_active(self):
        """True only when status is ACTIVE AND expiry has not passed."""
        return self.status == self.STATUS_ACTIVE and timezone.now() < self.expiry_time

    @property
    def time_remaining_seconds(self):
        """Seconds left until expiry (0 if already expired)."""
        delta = self.expiry_time - timezone.now()
        return max(0, int(delta.total_seconds()))

    @property
    def total_present(self):
        """Count of validated attendance records for this session."""
        return self.attendance_records.count()

    def close_session(self):
        """Manually close an attendance session."""
        self.status = self.STATUS_CLOSED
        self.save(update_fields=['status'])

    def auto_expire(self):
        """Mark session as expired (called from view layer if timer is done)."""
        self.status = self.STATUS_EXPIRED
        self.save(update_fields=['status'])


class Attendance(models.Model):
    """
    Individual attendance record — one per student per session.

    The combination of (session + roll_number) is unique, preventing
    duplicate submissions.
    """
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    full_name = models.CharField(max_length=150)
    roll_number = models.CharField(max_length=30)
    department = models.CharField(max_length=100)
    semester = models.PositiveSmallIntegerField()
    section = models.CharField(max_length=10)
    student_photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)

    # Security — stored for audit trail
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['marked_at']
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        # Prevent duplicate roll number in the same session
        unique_together = [('session', 'roll_number')]

    def __str__(self):
        return f"{self.roll_number} — {self.full_name} ({self.session.subject_name})"
