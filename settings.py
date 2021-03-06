from django.conf import global_settings

# stuff for email/seacucumber
EMAIL_BACKEND = 'seacucumber.backend.SESBackend'
SERVER_EMAIL = "visualvaccines@gmail.com"
CELERY_DISABLE_RATE_LIMITS = False
CUCUMBER_RATE_LIMIT = 1

# Django settings for the example project.
SDB_DOMAIN = 'papayacountrystocks'

DEBUG = False
TEMPLATE_DEBUG = False
ROOT_URLCONF = 'examples.urls'
TEMPLATE_DIRS = ('/home/ubuntu/vax/vaxapp/templates',)

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = 'vax'
DATABASE_USER = 'unicef'
DATABASE_PASSWORD = 'm3p3m3p3'
DATABASE_HOST = 'localhost'

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "unicef"
BROKER_PASSWORD = "m3p3m3p3"
BROKER_VHOST = "vaxlg"
CELERY_RESULT_BACKEND = "amqp"

DOCUMENT_UPLOAD_BUCKET = 'vaxtrack_uploads'
SERIALIZATION_MODULES = {'json-pretty': 'serializers.json_pretty'}

AUTH_PROFILE_MODULE = 'vaxapp.UserProfile'
LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/'

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en'
USE_I18N = True
USE_L10N = True
LANGUAGE_COOKIE_NAME = 'vaxtrack_lang'

gettext = lambda s: s

LANGUAGES = (
    ('fr', gettext('French')),
    ('en', gettext('English')),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/home/ubuntu/temp/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/assets/admin/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

# for debug_toolbar
INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'HIDE_DJANGO_SQL': False,
    'TAG': 'div',
}

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    #'vax.vaxapp.startup.StartupMiddlewareHack',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)

ROOT_URLCONF = 'vaxapp.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'vax.vaxapp',
    'south',
    'authority',
    'djcelery',
    'rosetta',
    'gunicorn',
    'seacucumber',
    'nexus',
    'gargoyle',
    #'debug_toolbar',
)
