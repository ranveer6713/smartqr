"""
WSGI config for smart_qr_attendance project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Patch sqlite3 with pysqlite3 for Vercel/serverless deployments
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_qr_attendance.settings')

application = get_wsgi_application()
app = application
