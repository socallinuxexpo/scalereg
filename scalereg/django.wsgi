import os
import sys

path = '/CHANGE_THIS!!!!!__path/to/parent_dir'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'scalereg.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
