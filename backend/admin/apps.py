from django.apps import AppConfig
import os


class AdminConfig(AppConfig):
    default_auto_field='django.db.models.BigAutoField'
    name='admin'

    def ready(self):
        if os.environ.get("RUN_MAIN")!="true":
            return
        from .events import start_watchers
        start_watchers()