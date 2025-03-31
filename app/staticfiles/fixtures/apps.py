from django.apps import AppConfig


class FixturesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fixtures'
    verbose_name = 'Fixtures Preventive Maintenance'

    def ready(self):
        import fixtures.signals
