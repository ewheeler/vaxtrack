#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import sys, os

from django.core.management import execute_manager

# use a default settings module if none was specified on the command line
DEFAULT_SETTINGS = 'settings'
settings_specified = any([arg.startswith('--settings=') for arg in sys.argv])
if not settings_specified and len(sys.argv) >= 2:
    sys.argv.append('--settings=%s' % DEFAULT_SETTINGS)

if __name__ == "__main__":
    project_root = os.path.abspath(
        os.path.dirname(__file__))

    sys.path.insert(0, project_root)

    import settings
    execute_manager(settings)
