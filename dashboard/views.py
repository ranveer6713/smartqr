"""
Dashboard app views.
The main landing page for logged-in faculty.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from attendance.models import AttendanceSession, Attendance


@login_required
def dashboard_home(request):
    """
    Main faculty dashboard.

    Gathers:
      - Active session for this faculty
      - Today's session count
      - Total attendance marked today
      - Recent attendance records
    """
    faculty = request.user
    today = timezone.localdate()

    # -----------------------------------------------------------------------
    # Active session — auto-expire lazily
    # -----------------------------------------------------------------------
    active_session = AttendanceSession.objects.filter(
        faculty=faculty,
        status=AttendanceSession.STATUS_ACTIVE,
    ).first()

    if active_session and not active_session.is_active:
        active_session.auto_expire()
        active_session = None

    # -----------------------------------------------------------------------
    # Today's sessions
    # -----------------------------------------------------------------------
    todays_sessions = AttendanceSession.objects.filter(
        faculty=faculty,
        start_time__date=today,
    ).order_by('-start_time')

    # -----------------------------------------------------------------------
    # Summary statistics
    # -----------------------------------------------------------------------
    total_sessions = AttendanceSession.objects.filter(faculty=faculty).count()

    total_attendance_today = Attendance.objects.filter(
        session__faculty=faculty,
        marked_at__date=today,
    ).count()

    # Recent 10 attendance records across all this faculty's sessions
    recent_attendance = Attendance.objects.filter(
        session__faculty=faculty
    ).select_related('session').order_by('-marked_at')[:10]

    context = {
        'faculty': faculty,
        'active_session': active_session,
        'todays_sessions': todays_sessions,
        'todays_session_count': todays_sessions.count(),
        'total_sessions': total_sessions,
        'total_attendance_today': total_attendance_today,
        'recent_attendance': recent_attendance,
        'now': timezone.localtime(),
    }
    return render(request, 'dashboard/home.html', context)
