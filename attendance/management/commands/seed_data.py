"""
Management command: seed_data

Creates:
  - A demo faculty user (username: faculty / password: faculty123)
  - Sample subjects
  - One past closed attendance session with 5 sample students

Usage:
    python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import FacultyProfile
from attendance.models import Subject, AttendanceSession, Attendance


class Command(BaseCommand):
    help = 'Seeds the database with demo data for development'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n[*] Seeding demo data...\n'))

        # ---------------------------------------------------------------
        # 1. Create superuser / admin
        # ---------------------------------------------------------------
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                password='admin123',
                email='admin@college.edu',
                first_name='Admin',
                last_name='User',
            )
            self.stdout.write(self.style.SUCCESS('[OK] Admin user created  -- admin / admin123'))
        else:
            self.stdout.write('[INFO] Admin already exists, skipping.')

        # ---------------------------------------------------------------
        # 2. Create demo faculty user
        # ---------------------------------------------------------------
        if not User.objects.filter(username='faculty').exists():
            faculty_user = User.objects.create_user(
                username='faculty',
                password='faculty123',
                email='faculty@college.edu',
                first_name='Prof. Rahul',
                last_name='Sharma',
            )
            FacultyProfile.objects.create(
                user=faculty_user,
                department='Computer Science Engineering',
                employee_id='EMP001',
                phone='9876543210',
            )
            self.stdout.write(self.style.SUCCESS('[OK] Faculty user created -- faculty / faculty123'))
        else:
            faculty_user = User.objects.get(username='faculty')
            self.stdout.write('[INFO] Faculty user already exists, skipping.')

        # ---------------------------------------------------------------
        # 3. Create subjects
        # ---------------------------------------------------------------
        subjects_data = [
            {'name': 'Data Structures and Algorithms', 'code': 'CS301', 'department': 'CSE', 'semester': 3},
            {'name': 'Database Management Systems',    'code': 'CS302', 'department': 'CSE', 'semester': 3},
            {'name': 'Operating Systems',              'code': 'CS401', 'department': 'CSE', 'semester': 4},
            {'name': 'Computer Networks',              'code': 'CS402', 'department': 'CSE', 'semester': 4},
            {'name': 'Software Engineering',           'code': 'CS501', 'department': 'CSE', 'semester': 5},
            {'name': 'Artificial Intelligence',        'code': 'CS601', 'department': 'CSE', 'semester': 6},
            {'name': 'Machine Learning',               'code': 'CS602', 'department': 'CSE', 'semester': 6},
            {'name': 'Engineering Mathematics',        'code': 'MA201', 'department': 'MATH', 'semester': 2},
        ]

        for s in subjects_data:
            Subject.objects.get_or_create(code=s['code'], defaults=s)

        self.stdout.write(self.style.SUCCESS(f'[OK] {len(subjects_data)} subjects created/verified'))

        # ---------------------------------------------------------------
        # 4. Create a past closed session with 5 students
        # ---------------------------------------------------------------
        past_start = timezone.now() - timezone.timedelta(hours=2)
        past_expiry = past_start + timezone.timedelta(minutes=15)

        session, created = AttendanceSession.objects.get_or_create(
            faculty=faculty_user,
            subject_name='Data Structures and Algorithms',
            start_time__date=past_start.date(),
            defaults={
                'subject': Subject.objects.filter(code='CS301').first(),
                'branch': 'Computer Science Engineering',
                'semester': 3,
                'section': 'A',
                'classroom': 'CS-301',
                'duration_minutes': 15,
                'expiry_time': past_expiry,
                'status': AttendanceSession.STATUS_CLOSED,
            }
        )

        if created:
            # Add sample students
            students = [
                ('CS2021001', 'Amit Kumar',    'CSE', 3, 'A'),
                ('CS2021002', 'Priya Singh',   'CSE', 3, 'A'),
                ('CS2021003', 'Rohit Verma',   'CSE', 3, 'A'),
                ('CS2021004', 'Anjali Mishra', 'CSE', 3, 'A'),
                ('CS2021005', 'Rahul Gupta',   'CSE', 3, 'A'),
            ]

            for roll, name, dept, sem, sec in students:
                Attendance.objects.get_or_create(
                    session=session,
                    roll_number=roll,
                    defaults={
                        'full_name': name,
                        'department': dept,
                        'semester': sem,
                        'section': sec,
                        'ip_address': '192.168.1.10',
                    }
                )
            self.stdout.write(self.style.SUCCESS('[OK] Demo session with 5 students created'))
        else:
            self.stdout.write('[INFO] Demo session already exists, skipping.')

        self.stdout.write(self.style.SUCCESS('\n[OK] Demo data seeding complete!\n'))
        self.stdout.write(self.style.WARNING(
            'Login credentials:\n'
            '  Admin   -- username: admin    password: admin123\n'
            '  Faculty -- username: faculty  password: faculty123\n'
        ))
