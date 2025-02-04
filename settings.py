ALLOWED_HOSTS = ['*', '.amplifyapp.com']

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Debug設定
DEBUG = False  # 本番環境ではFalse

# CSRF設定
CSRF_TRUSTED_ORIGINS = ['https://*.amplifyapp.com'] 