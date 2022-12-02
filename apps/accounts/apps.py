from django.apps import AppConfig
# from django.core.management import call_command


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    # def ready(self):
    #     call_command('create_groups')
