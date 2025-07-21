from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'SMS-to-AI Agent Core'
    
    def ready(self):
        """Initialize the app when Django starts"""
        pass 