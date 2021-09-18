import os
import json
import sys
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ImproperlyConfigured
from myproject.apps.core.versioning import get_git_changeset_timestamp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXTERNAL_BASE = os.path.join(BASE_DIR, "externals")
EXTERNAL_LIBS_PATH = os.path.join(EXTERNAL_BASE, "libs")
EXTERNAL_APPS_PATH = os.path.join(EXTERNAL_BASE, "apps")
sys.path = ["", EXTERNAL_LIBS_PATH, EXTERNAL_APPS_PATH] + sys.path


with open(os.path.join(os.path.dirname(__file__), 'secrets.json'), 'r') as f:
    secrets = json.loads(f.read())


def get_secret(setting):

    try:
        return secrets[setting]
    except KeyError:
        error_msg = f'Set the {setting} secret variable'
        raise ImproperlyConfigured(error_msg)



SECRET_KEY = get_secret('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "0.0.0.0",
]


# Application definition

INSTALLED_APPS = [
    # contributed
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
	"django.forms",
	"django_json_ld",
    # third-party
	"imagekit",
	"qr_code",
	"haystack",
    # ...
    # local
    "myproject.apps.magazine",
	"myproject.apps.core",
	"myproject.apps.ideas",
	"myproject.apps.categories",
	"myproject.apps.search",
	"crispy_forms",
	"django_elasticsearch_dsl",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "myproject", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "myproject.apps.core.context_processors.website_url",
            ]
        },
    }
]
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
WSGI_APPLICATION = 'myproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
		'NAME': 'mydatabase',
       # 'NAME': get_secret('DATABASE_NAME'),
        'USER': get_secret('DATABASE_USER'),
        'PASSWORD': get_secret('DATABASE_PASSWORD'),
        'HOST': 'db',
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

LANGUAGES = [
    ("bg", "Bulgarian"),    ("hr", "Croatian"),
    ("cs", "Czech"),        ("da", "Danish"),
    ("nl", "Dutch"),        ("en", "English"),
    ("et", "Estonian"),     ("fi", "Finnish"),
    ("fr", "French"),       ("de", "German"),
    ("el", "Greek"),        ("hu", "Hungarian"),
    ("ga", "Irish"),        ("it", "Italian"),
    ("lv", "Latvian"),      ("lt", "Lithuanian"),
    ("mt", "Maltese"),      ("pl", "Polish"),
    ("pt", "Portuguese"),   ("ro", "Romanian"),
    ("sk", "Slovak"),       ("sl", "Slovene"),
    ("es", "Spanish"),      ("sv", "Swedish"),
]

HAYSTACK_CONNECTIONS = {}
for lang_code, lang_name in LANGUAGES:
    lang_code_underscored = lang_code.replace("-", "_")
    HAYSTACK_CONNECTIONS[f"default_{lang_code_underscored}"] = {
        "ENGINE": "myproject.apps.search.multilingual_whoosh_backend.MultilingualWhooshEngine",
        "PATH": os.path.join(BASE_DIR, "tmp", f"whoosh_index_{lang_code_underscored}"),
    }
lang_code_underscored = LANGUAGE_CODE.replace("-", "_")
HAYSTACK_CONNECTIONS["default"] = HAYSTACK_CONNECTIONS[
    f"default_{lang_code_underscored}"
]

ELASTICSEARCH_DSL={
	'default': { 'hosts': 'localhost:9200' },
	}

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'myproject', 'site_static'),
]

timestamp = get_git_changeset_timestamp(BASE_DIR)
STATIC_URL = f'/static/{timestamp}/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CRISPY_TEMPLATE_PACK = "bootstrap4"

MAGAZINE_ARTICLE_THEME_CHOICES = [
    ('futurism', _("Futurism")),
    ('nostalgia', _("Nostalgia")),
    ('sustainability', _("Sustainability")),
    ('wonder', _("Wonder")),
    ('positivity', _("Positivity")),
    ('solutions', _("Solutions")),
    ('science', _("Science")),
]

EMAIL_HOST = get_secret("EMAIL_HOST")
EMAIL_PORT = get_secret("EMAIL_PORT")
EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_secret("EMAIL_HOST_PASSWORD")
