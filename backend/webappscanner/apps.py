from django.apps import AppConfig

class WebappscannerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webappscanner'

    def ready(self):
        # Auto-start ZAP in development only
        from django.conf import settings
        if not getattr(settings, "DEBUG", False):
            return
        try:
            import webappscanner.zap_launcher as zap_launcher
            try:
                zap_launcher.start_zap(wait=True)
            except Exception as e:
                # don't crash server startup; just warn
                print("Warning: zap_launcher.start_zap failed:", e)
        except Exception as e:
            # If import fails, print and continue
            print("Warning: could not import zap_launcher:", e)
