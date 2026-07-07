"""
Attendance app utility functions.

Centralises:
  - QR code image generation
  - IP address extraction
  - Network validation
"""

import io
import os
import socket

import qrcode
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile


def get_local_ip():
    """
    Attempt to determine the machine's local network IP address.
    Works offline (for college LAN labs) by falling back to hostname resolution.
    Falls back to '127.0.0.1' if no network interface is active.
    """
    # Method 1: Socket connection to public DNS (requires routing, works online)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith('127.'):
            return ip
    except OSError:
        pass

    # Method 2: Resolve hostname (works offline on Windows/Linux LANs)
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and not ip.startswith('127.'):
            return ip
    except OSError:
        pass

    # Method 3: Iterate address info for hostname (works offline)
    try:
        for ip_info in socket.getaddrinfo(socket.gethostname(), None):
            val = ip_info[4][0]
            if not val.startswith('127.') and not ':' in val:
                return val
    except OSError:
        pass

    return '127.0.0.1'


def get_client_ip(request):
    """
    Extract the real client IP address from the request.
    Handles proxy headers (X-Forwarded-For) for reverse-proxy setups.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first (original client) IP from the chain
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def is_allowed_network(ip_address):
    """
    Validate that the student's IP belongs to the allowed college network.

    If ALLOWED_NETWORK_PREFIX is None in settings, all IPs are accepted
    (useful for development / testing).

    In production, set ALLOWED_NETWORK_PREFIX = '192.168.' (or your LAN range).
    """
    allowed_prefix = getattr(settings, 'ALLOWED_NETWORK_PREFIX', None)
    if not allowed_prefix:
        return True   # Network restriction disabled
    return ip_address.startswith(allowed_prefix)


def generate_qr_code(session, request):
    """
    Generate a QR code image for the given AttendanceSession.

    The QR encodes a URL of the form:
        http://<local-ip>:<port>/attendance/<session_id>/<token>/

    The image is saved to the session's qr_code ImageField.

    Args:
        session  : AttendanceSession instance
        request  : HttpRequest — used to build an absolute URL

    Returns:
        The updated session instance.
    """
    local_ip = get_local_ip()
    port = request.META.get('SERVER_PORT', '8000')

    # Build the attendance URL students will scan
    attendance_url = (
        f"http://{local_ip}:{port}/attendance/"
        f"{session.session_id}/{session.token}/"
    )

    # --- QR Code generation ---
    qr = qrcode.QRCode(
        version=None,             # auto-determine size
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,
        border=4,
    )
    qr.add_data(attendance_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='#1a1a2e', back_color='white')

    # Convert to RGBA for compatibility then save as PNG bytes
    img = img.convert('RGB')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    # Save to the model's ImageField
    filename = f"qr_{session.session_id}.png"
    session.qr_code.save(filename, ContentFile(buffer.read()), save=True)

    return session, attendance_url
