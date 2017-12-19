"""Settings that need to be set in order to run the tests."""
import os

def get_env_setting(setting, default):
    """ Get the environment setting or return exception """
    try:
        return os.environ[setting]
    except KeyError:
        return default

TMDB_API_KEY=get_env_setting('TMDB_API_KEY', '626b3a716f2469415c3d5b26433d445c')
TMDB_SESSION_ID=get_env_setting('TMDB_SESSION_ID', '')

DEBUG = True
SITE_ID = 1

APP_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ROOT_URLCONF = 'tmdb.tests.urls'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(APP_ROOT, '../static')
MEDIA_ROOT = os.path.join(APP_ROOT, '../media')
STATICFILES_DIRS = (
    os.path.join(APP_ROOT, 'static'),
)

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'DIRS': [os.path.join(APP_ROOT, 'tests/test_app/templates')],
    'OPTIONS': {
        'context_processors': (
            'django.contrib.auth.context_processors.auth',
            'django.template.context_processors.request',
        )
    }
}]

EXTERNAL_APPS = [
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
]

INTERNAL_APPS = [
    'django_tmdb',
    'django_tmdb.tests.test_app',
]

INSTALLED_APPS = EXTERNAL_APPS + INTERNAL_APPS

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

SECRET_KEY = 'foobar'
