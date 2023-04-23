"""
WSGI config for cs50fp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys
import socket

from static_ranges import Ranges
from django.core.wsgi import get_wsgi_application
from dj_static import Cling, MediaCling

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cs50fp.settings')

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
print(f"Your Computer IP Address is: http://{IPAddr}{':' + sys.argv[-1].split(':')[-1] if sys.argv[-1].split(':')[-1] != '80' else ''}/")


# application = get_wsgi_application()
application = Ranges(Cling(MediaCling(get_wsgi_application())))

