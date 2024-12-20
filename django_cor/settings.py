"""
Django settings for django_cor project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-39^%wf)$9v-xck8rxos3db46$c7fp@c=_eq_)+y&8jfr=e)&k%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

CSRF_TRUSTED_ORIGINS = ['http://*', 'https://*']

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mi_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console':{
            'class':'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',  # Путь к вашему файлу логов
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',  # Установите нужный уровень логирования
            'propagate': True,
        },
    },
}

ROOT_URLCONF = 'django_cor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_cor.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

import os
import sys  # Добавлено для проверки аргументов командной строки

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'django_db',           # Имя базы данных
        'USER': 'postgres',            # Имя пользователя базы данных
        'PASSWORD': '220689',  # Пароль пользователя
        'HOST': 'db_app2',             # Имя хоста базы данных (имя Docker-сервиса)
        'PORT': '5432',                # Порт подключения к PostgreSQL
    }
}

#
# if 'test' in sys.argv or 'test_coverage' in sys.argv:
#     # Настройки базы данных для тестов
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': ':memory:',  # Использование базы данных в памяти для тестов
#         }
#     }
# else:
#     # Основные настройки базы данных
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': os.environ.get('DATABASE_NAME', 'django_db'),
#             'USER': os.environ.get('DATABASE_USER', 'postgres'),
#             'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
#             'HOST': os.environ.get('DATABASE_HOST', 'db_app2'),
#             'PORT': os.environ.get('DATABASE_PORT', '5432'),
#         }
#     }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_URL = '/media/'  # URL для доступа к медиафайлам
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Папка для хранения медиафайлов

STATIC_ROOT = BASE_DIR
STATIC_URL = '/static/'

# URL перенаправления после входа и выхода
LOGIN_URL = '/accounts/login/'        # URL страницы входа
LOGIN_REDIRECT_URL = '/'              # URL после успешного входа
LOGOUT_REDIRECT_URL = '/'             # URL после выхода

# Дополнительные настройки
DEFAULT_PRICE_PER_KB = 1.0  # Цена по умолчанию

# Настройка URL для FastAPI
if 'test' in sys.argv or 'test_coverage' in sys.argv:
    FASTAPI_BASE_URL = "http://localhost:8000"  # При тестировании используем локальный адрес
else:
    FASTAPI_BASE_URL = "http://web:8000"  # Используйте имя контейнера FastAPI


PROXY_BASE_URL = 'http://djangorest:8002'
# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

print(f"MEDIA_ROOT: {MEDIA_ROOT}")