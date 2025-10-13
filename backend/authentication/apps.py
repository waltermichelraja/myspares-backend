from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field='django.db.models.BigAutoField'
    name='authentication'

    COOKIE_SETTINGS={
    "httponly": True,
    "secure": True,
    "samesite": "Strict",
    "path": "/api/auth/"
}