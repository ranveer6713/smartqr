"""
Attendance app views.

Views:
  - create_session       : Faculty creates a new attendance session
  - session_qr           : Displays the QR code with countdown timer
  - close_session        : Faculty manually closes a session
  - mark_attendance      : Student fills the attendance form (no login needed)
  - attendance_success   : Confirmation page shown to student
  - attendance_already   : Page shown when duplicate submission detected
  - attendance_closed    : Page shown when session is expired/closed
  - session_detail       : Faculty views live attendance list for a session
  - delete_attendance    : Faculty removes an incorrect attendance entry
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import IntegrityError

from .models import AttendanceSession, Attendance
from .forms import AttendanceSessionForm, StudentAttendanceForm
from .utils import generate_qr_code, get_client_ip, is_allowed_network


# ===========================================================================
# Faculty views (login required)
# ===========================================================================

@login_required
def create_session(request):
    """
    Faculty creates a new attendance session.
    Enforces one-active-session-per-faculty rule.
    """
    # Check if faculty already has an active session
    existing_active = AttendanceSession.objects.filter(
        faculty=request.user,
        status=AttendanceSession.STATUS_ACTIVE,
    ).first()

    # Auto-expire sessions whose timer has passed
    if existing_active and not existing_active.is_active:
        existing_active.auto_expire()
        existing_active = None

    if existing_active:
        messages.warning(
            request,
            f'You already have an active session for "{existing_active.subject_name}". '
            f'Please close it before creating a new one.'
        )
        return redirect('attendance:session_qr', pk=existing_active.pk)

    if request.method == 'POST':
        form = AttendanceSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.faculty = request.user
            # Calculate expiry time from duration
            session.expiry_time = timezone.now() + timezone.timedelta(
                minutes=session.duration_minutes
            )
            session.save()

            messages.success(request, 'Attendance session created successfully!')
            return redirect('attendance:session_qr', pk=session.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = AttendanceSessionForm()

    return render(request, 'attendance/create_session.html', {'form': form})


@login_required
def session_qr(request, pk):
    """
    Display the QR code page for the given session.
    Also shows session details, countdown timer, and live attendance count.
    The faculty sees this on the projector.
    """
    session = get_object_or_404(AttendanceSession, pk=pk, faculty=request.user)

    # Auto-expire if timer has elapsed (lazy expiry check)
    if session.status == AttendanceSession.STATUS_ACTIVE and not session.is_active:
        session.auto_expire()

    # Reload to get fresh status
    session.refresh_from_db()

    student_url = session.get_student_url(request)
    
    # Determine if localhost warning should be shown (based on request hostname)
    host = request.get_host().split(':')[0]
    is_localhost = host in ['127.0.0.1', 'localhost']

    context = {
        'session': session,
        'time_remaining': session.time_remaining_seconds,
        'attendance_list': session.attendance_records.order_by('-marked_at'),
        'student_url': student_url,
        'is_localhost': is_localhost,
    }
    return render(request, 'attendance/session_qr.html', context)


@login_required
def session_qr_image(request, pk):
    """
    Generate the QR code image dynamically in-memory and return it as a PNG response.
    Requires no disk writes, making it compatible with Vercel serverless functions.
    """
    session = get_object_or_404(AttendanceSession, pk=pk, faculty=request.user)
    student_url = session.get_student_url(request)
    
    import io
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
    
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_required
def close_session(request, pk):
    """Faculty manually closes an attendance session."""
    session = get_object_or_404(AttendanceSession, pk=pk, faculty=request.user)

    if request.method == 'POST':
        session.close_session()
        messages.success(request, f'Session for "{session.subject_name}" has been closed.')
        return redirect('dashboard:home')

    return render(request, 'attendance/confirm_close.html', {'session': session})


@login_required
def session_detail(request, pk):
    """
    Live attendance list for a session.
    Faculty can search students and remove incorrect entries.
    """
    session = get_object_or_404(AttendanceSession, pk=pk, faculty=request.user)

    # Auto-expire if timer passed
    if session.status == AttendanceSession.STATUS_ACTIVE and not session.is_active:
        session.auto_expire()
        session.refresh_from_db()

    # Search functionality
    query = request.GET.get('q', '').strip()
    attendance_qs = session.attendance_records.order_by('roll_number')
    if query:
        attendance_qs = attendance_qs.filter(
            roll_number__icontains=query
        ) | attendance_qs.filter(
            full_name__icontains=query
        )

    context = {
        'session': session,
        'attendance_list': attendance_qs,
        'total_present': session.total_present,
        'query': query,
        'time_remaining': session.time_remaining_seconds,
    }
    return render(request, 'attendance/session_detail.html', context)


@login_required
def delete_attendance(request, session_pk, attendance_pk):
    """
    Faculty removes an incorrect attendance entry.
    Only allowed via POST to prevent accidental GET-based deletion.
    """
    session = get_object_or_404(AttendanceSession, pk=session_pk, faculty=request.user)
    attendance = get_object_or_404(Attendance, pk=attendance_pk, session=session)

    if request.method == 'POST':
        roll = attendance.roll_number
        attendance.delete()
        messages.success(request, f'Attendance for Roll No. {roll} has been removed.')
        return redirect('attendance:session_detail', pk=session_pk)

    return render(request, 'attendance/confirm_delete_attendance.html', {
        'attendance': attendance,
        'session': session,
    })


# ===========================================================================
# Student views (no login required)
# ===========================================================================

def mark_attendance(request, session_id, token):
    """
    Student attendance form page.

    Validates:
      1. Session exists and token matches
      2. Session is currently active (not expired or closed)
      3. Student's IP is on the allowed network
      4. IP address hasn't already submitted for this session (one device = one entry)
      5. Roll number hasn't already been submitted

    On success: saves record and shows confirmation.
    """
    # Fetch the session — return 404 if session_id or token don't match
    session = get_object_or_404(
        AttendanceSession,
        session_id=session_id,
        token=token
    )

    # Lazy auto-expire check
    if session.status == AttendanceSession.STATUS_ACTIVE and not session.is_active:
        session.auto_expire()
        session.refresh_from_db()

    # Session is closed or expired
    if not session.is_active:
        return render(request, 'attendance/attendance_closed.html', {'session': session})

    # Network validation
    client_ip = get_client_ip(request)
    if not is_allowed_network(client_ip):
        return render(request, 'attendance/network_error.html', {
            'ip': client_ip,
        })

    # IP-based duplicate prevention — one device (IP) per session
    # Skip this check for loopback/localhost to allow local testing
    if not client_ip.startswith('127.') and client_ip != 'localhost':
        already_submitted_by_ip = session.attendance_records.filter(
            ip_address=client_ip
        ).first()
        if already_submitted_by_ip:
            return render(request, 'attendance/ip_already_marked.html', {
                'session': session,
                'existing_record': already_submitted_by_ip,
            })

    if request.method == 'POST':
        form = StudentAttendanceForm(request.POST, request.FILES, session=session)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.session = session
            attendance.ip_address = client_ip

            try:
                attendance.save()
                return redirect('attendance:attendance_success', session_id=session_id)
            except IntegrityError:
                # Roll number already exists for this session
                return render(request, 'attendance/attendance_already.html', {
                    'session': session,
                    'roll_number': form.cleaned_data.get('roll_number'),
                })
    else:
        # Pre-fill department/semester/section from session to help students
        form = StudentAttendanceForm(initial={
            'department': session.branch,
            'semester': session.semester,
            'section': session.section,
        }, session=session)

    context = {
        'form': form,
        'session': session,
        'time_remaining': session.time_remaining_seconds,
    }
    return render(request, 'attendance/mark_attendance.html', context)


def attendance_success(request, session_id):
    """
    Simple confirmation page shown after successful submission.
    Fetches session for display context.
    """
    session = get_object_or_404(AttendanceSession, session_id=session_id)
    return render(request, 'attendance/attendance_success.html', {'session': session})
