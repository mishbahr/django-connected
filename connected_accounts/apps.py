from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ConnectedAccountsConfig(AppConfig):
    name = 'connected_accounts'
    verbose_name = _('Connected Accounts')
