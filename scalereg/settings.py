# Django settings for scalereg project.

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = False

# Additional debug logging for sales transactions
# Set to True to enable.
SCALEREG_DEBUG_LOGGING_ENABLED = False
SCALEREG_DEBUG_LOGGING_PATH = '/tmp/scale_reg.log'

ALLOWED_HOSTS = ['*']

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # 'django.db.backends.mysql', 'django.db.backends.postgresql', 'django.db.backends.sqlite3', or 'django.db.backends.oracle'
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),  # Or path to database file if using sqlite3.
        'USER': '', # Not used with sqlite3.
        'PASSWORD': '',  # Not used with sqlite3.
        'HOST': '', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '', # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: '/home/media/media.lawrence.com/'
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: 'http://media.lawrence.com', 'http://example.com/media/'
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: 'http://foo.com/media/', '/media/'.

STATIC_URL = 'https://register.socallinuxexpo.org/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'scalereg/media')]

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'CHANGE_THIS!!!!!__ANY_VALID_PYTHON_STRING_WORKS'

MIDDLEWARE = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'scalereg.urls'

TEMPLATES = [
  {
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_DIR, 'scalereg/scale_templates')],
    'APP_DIRS': True,
    'OPTIONS': {
      'context_processors': [
        'django.contrib.messages.context_processors.messages',
        'django.contrib.auth.context_processors.auth',
      ]
    },
  },
]

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'scalereg.auth_helper',
    'scalereg.reg6',
    'scalereg.reports',
    'scalereg.sponsorship',
)

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Optional questions about PGP keys for a PGP Key Signing Party.
#
# Integer value corresponding to the first PGP question. Set to -1 to disable.
# The questions must have consecutive IDs:
# Text: What is your PGP fingerprint?
# Text: What is your PGP fingerprint size? (number of bits)
# List: What is your PGP fingerprint type? / [DSA, RSA]
# Text: What is your second PGP fingerprint?
# Text: What is your second PGP fingerprint size? (number of bits)
# List: What is your second PGP fingerprint type? / [DSA, RSA]
# ...
SCALEREG_PGP_QUESTION_ID_START = -1

# Positive integer value indicating max number of PGP keys allowed.
SCALEREG_PGP_MAX_KEYS = 0

# The PGP Key Signing Party addon item name.
SCALEREG_PGP_KSP_ITEM_NAME = 'KSP'

# PayFlow Account Settings must be set to use PayFlow.
#
# PayFlow URL:
SCALEREG_PAYFLOW_URL = 'https://payflowlink.paypal.com/'
# Manager User Login:
SCALEREG_PAYFLOW_LOGIN = ''
# Partner (either Paypal or Verisign):
SCALEREG_PAYFLOW_PARTNER = ''

# Secret used for express check-in and scanned badges.
SCALEREG_EXPRESS_CHECKIN_SECRET = ''

# Secret used in browser user agent for identifying kiosks.
SCALEREG_KIOSK_AGENT_SECRET = 'CHANGE_ME:'

# URL for the sponsorship agreement document.
SCALEREG_SPONSORSHIP_AGREEMENT_URL = 'CHANGE_THIS_URL'

# Set to True if you want scalereg to be able to email attendees.
# You need to set EMAIL_HOST, EMAIL_PORT, and other EMAIL_ settings
# appropriately.
SCALEREG_SEND_MAIL = False
# You also need to set the from address below:
SCALEREG_EMAIL = ''

# List of tickets to apply promo codes to in the admin interface.
SCALEREG_ADMIN_TICKETS_FOR_PROMO = []

# Increasing limit to work around Django bug with TemporaryFileUploadHandler.
#FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20 MB
