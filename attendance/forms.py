"""
Attendance app forms.

Forms:
  - AttendanceSessionForm  : Faculty creates a new session
  - StudentAttendanceForm  : Student fills in their details to mark attendance
"""

from django import forms
from django.utils import timezone

from .models import AttendanceSession, Subject, Attendance


class AttendanceSessionForm(forms.ModelForm):
    """
    Form for faculty to create a new attendance session.
    Subject field is a dropdown populated from the Subject model.
    """

    class Meta:
        model = AttendanceSession
        fields = [
            'subject', 'subject_name', 'branch',
            'semester', 'section', 'classroom', 'duration_minutes', 'meeting_link', 'require_photo'
        ]
        widgets = {
            'subject': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_subject',
            }),
            'subject_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Data Structures and Algorithms',
                'id': 'id_subject_name',
            }),
            'branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Computer Science Engineering',
            }),
            'semester': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 8,
                'placeholder': '1–8',
            }),
            'section': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. A, B, C',
            }),
            'classroom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. CS-301',
            }),
            'duration_minutes': forms.Select(attrs={
                'class': 'form-select',
            }),
            'meeting_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. https://meet.google.com/abc-defg-hij',
            }),
            'require_photo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
                'id': 'id_require_photo',
            }),
        }
        labels = {
            'subject': 'Subject (optional — select from list)',
            'subject_name': 'Subject Name',
            'branch': 'Branch / Department',
            'semester': 'Semester',
            'section': 'Section',
            'classroom': 'Classroom / Room Number',
            'duration_minutes': 'Attendance Duration',
            'meeting_link': 'Meeting Link (Optional — Google Meet / Zoom)',
            'require_photo': 'Require Student Photo Submission',
        }

    def clean_semester(self):
        """Validate semester is between 1 and 8."""
        sem = self.cleaned_data.get('semester')
        if sem and (sem < 1 or sem > 8):
            raise forms.ValidationError('Semester must be between 1 and 8.')
        return sem

    def clean_subject_name(self):
        """Ensure subject name is not empty."""
        name = self.cleaned_data.get('subject_name', '').strip()
        if not name:
            raise forms.ValidationError('Please enter the subject name.')
        return name


class StudentAttendanceForm(forms.ModelForm):
    """
    Form presented to students when they scan a QR code.
    No authentication required — just basic identity details.
    """

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        if session and session.require_photo:
            self.fields['student_photo'].required = True
        else:
            self.fields.pop('student_photo', None)

    class Meta:
        model = Attendance
        fields = ['full_name', 'roll_number', 'department', 'semester', 'section', 'student_photo']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter your full name',
                'autocomplete': 'name',
            }),
            'roll_number': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. CS2021001',
                'style': 'text-transform: uppercase;',
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. Computer Science Engineering',
            }),
            'semester': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'min': 1,
                'max': 8,
            }),
            'section': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. A',
                'style': 'text-transform: uppercase;',
            }),
            'student_photo': forms.FileInput(attrs={
                'class': 'form-control form-control-lg',
                'accept': 'image/*',
                'capture': 'user',
            }),
        }
        labels = {
            'full_name': 'Full Name',
            'roll_number': 'Roll Number',
            'department': 'Department',
            'semester': 'Semester',
            'section': 'Section',
            'student_photo': 'Take/Upload Photo',
        }

    def clean_roll_number(self):
        """Normalize roll number to uppercase."""
        return self.cleaned_data.get('roll_number', '').strip().upper()

    def clean_section(self):
        """Normalize section to uppercase."""
        return self.cleaned_data.get('section', '').strip().upper()

    def clean_semester(self):
        """Validate semester range."""
        sem = self.cleaned_data.get('semester')
        if sem and (sem < 1 or sem > 8):
            raise forms.ValidationError('Please enter a valid semester (1–8).')
        return sem
