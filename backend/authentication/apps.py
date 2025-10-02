from django.apps import AppConfig
import os


class AuthenticationConfig(AppConfig):
    default_auto_field='django.db.models.BigAutoField'
    name='authentication'

    COOKIE_SETTINGS={
    "httponly": True,
    "secure": True,
    "samesite": "Strict",
    "path": "/api/auth/"
}

    def ready(self):
        if os.environ.get("RUN_MAIN")!="true":
            return
        from .models import TokenManager
        try:
            TokenManager.cleanup_old_tokens(days=14)
        except Exception as e:
            print(f"[Startup Error] failed to cleanup tokens: {e}")