from django.utils.translation import ugettext_lazy as _

from connected_accounts.conf import settings
from connected_accounts.provider_pool import providers

from .base import OAuth2Provider, ProviderAccount


class InstagramAccount(ProviderAccount):
    PROFILE_URL = 'http://instagram.com/'

    def get_profile_url(self):
        return self.PROFILE_URL + self.account.extra_data.get('username', '')

    def get_avatar_url(self):
        return self.account.extra_data.get('profile_picture')

    def to_str(self):
        default = super(InstagramAccount, self).to_str()
        return self.account.extra_data.get('username', default)

    def extract_common_fields(self):
        data = self.account.extra_data
        return dict(username=data.get('username'),
                    name=data.get('full_name'))


class InstagramProvider(OAuth2Provider):
    id = 'instagram'
    name = _('Instagram')
    account_class = InstagramAccount

    access_token_url = 'https://api.instagram.com/oauth/access_token'
    authorization_url = 'https://api.instagram.com/oauth/authorize'
    profile_url = 'https://api.instagram.com/v1/users/self'

    consumer_key = settings.CONNECTED_ACCOUNTS_INSTAGRAM_CONSUMER_KEY
    consumer_secret = settings.CONNECTED_ACCOUNTS_INSTAGRAM_CONSUMER_SECRET
    scope = settings.CONNECTED_ACCOUNTS_INSTAGRAM_SCOPE

    def extract_uid(self, data):
        return str(data['data']['id'])

    def extract_extra_data(self, data):
        return data.get('data', {})


providers.register(InstagramProvider)
