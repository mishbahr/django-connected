from django.utils.translation import ugettext_lazy as _

from connected_accounts.conf import settings
from connected_accounts.provider_pool import providers

from .base import OAuth2Provider, ProviderAccount


class BitlyAccount(ProviderAccount):
    def get_profile_url(self):
        return self.account.extra_data.get('profile_url')

    def get_avatar_url(self):
        return settings.STATIC_URL + 'img/connected_accounts/providers/bitly.png'

    def to_str(self):
        default = super(BitlyAccount, self).to_str()
        return self.account.extra_data.get('full_name', default)

    def extract_common_fields(self):
        data = self.account.extra_data
        return dict(username=data['login'],
                    name=data.get('full_name'))


class BitlyProvider(OAuth2Provider):
    id = 'bitly'
    name = _('Bitly')
    account_class = BitlyAccount

    access_token_url = 'https://api-ssl.bitly.com/oauth/access_token'
    authorization_url = 'https://bitly.com/oauth/authorize'
    profile_url = 'https://api-ssl.bitly.com/v3/user/info'

    consumer_key = settings.CONNECTED_ACCOUNTS_BITLY_CONSUMER_KEY
    consumer_secret = settings.CONNECTED_ACCOUNTS_BITLY_CONSUMER_SECRET

    def extract_uid(self, data):
        return str(data['data']['login'])

    def extract_extra_data(self, data):
        return data.get('data', {})

providers.register(BitlyProvider)
