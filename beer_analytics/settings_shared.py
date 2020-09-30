import platform
from pathlib import Path

from environ import Env

env = Env()
env.read_env()

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

SECRET_KEY = env.str('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
DEBUG = True

INSTALLED_APPS = [
    'recipe_db.apps.RecipeDbConfig',
    'web_app.apps.WebAppConfig',
    'django.contrib.humanize',
    'web_app.apps.WebAppStaticFilesConfig',
    'pipeline',
]

try:
    import data_import
    INSTALLED_APPS.append('data_import.apps.DataImportConfig')
except ModuleNotFoundError:
    pass

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'beer_analytics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'beer_analytics.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'var/beer_analytics.sqlite3',
    },
    'data_import': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'var/data_import.sqlite3',
    }
}
DATABASE_ROUTERS = ['beer_analytics.DataImportRouter']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': env.str('LOG_FILE'),
        },
    },
    'root': {
        'handlers': ['file'],
        'level': env.str('LOG_LEVEL'),
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': env.str('LOG_LEVEL'),
            'propagate': False,
        },
    },
}

CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 60 * 60 * 12
CACHE_MIDDLEWARE_KEY_PREFIX = ''

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = True
USE_TZ = False
USE_THOUSAND_SEPARATOR = True
NUMBER_GROUPING = 3

STATIC_URL = '/static/'
STATIC_ROOT = 'static'
STATICFILES_STORAGE = 'pipeline.storage.PipelineManifestStorage'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)

PIPELINE = {
    'PIPELINE_ENABLED': False,
    'CSS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
    'JS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
    'DISABLE_WRAPPER': True,
    'COMPILERS': (
      'pipeline.compilers.sass.SASSCompiler',
    ),
    'YUGLIFY_BINARY': str(BASE_DIR / "node_modules/.bin/yuglify") + (".cmd" if platform.system() == "Windows" else ""),
    'SASS_BINARY': str(BASE_DIR / "node_modules/.bin/sass") + (".cmd" if platform.system() == "Windows" else ""),
    'STYLESHEETS': {
        'base': {
            'source_filenames': (
                'scss/beer_analytics.scss',
            ),
            'output_filename': 'css/style.css',
        },
    },
    'JAVASCRIPT': {
        'app': {
            'source_filenames': (
                'js/application.js',
            ),
            'output_filename': 'js/app.js',
        }
    }
}

RAW_DATA_DIR = env.str('RAW_DATA_DIR')
