import logging

from django.utils.translation import ugettext_lazy as _

from connected_accounts.conf import settings
from connected_accounts.provider_pool import providers

from .base import OAuth2Provider, ProviderAccount

logger = logging.getLogger('connected_accounts')


class GoogleAccount(ProviderAccount):
    def get_profile_url(self):
        return self.account.extra_data.get('link')

    def get_avatar_url(self):
        return self.account.extra_data.get('picture')

    def to_str(self):
        default = super(GoogleAccount, self).to_str()
        return self.account.extra_data.get('name', default)

    def extract_common_fields(self):
        data = self.account.extra_data
        return dict(email=data.get('email'),
                    last_name=data.get('family_name'),
                    first_name=data.get('given_name'))


class GoogleProvider(OAuth2Provider):
    id = 'google'
    name = _('Google+')
    account_class = GoogleAccount

    authorization_url = 'https://accounts.google.com/o/oauth2/auth'
    access_token_url = 'https://accounts.google.com/o/oauth2/token'
    profile_url = 'https://www.googleapis.com/oauth2/v1/userinfo'

    consumer_key = settings.CONNECTED_ACCOUNTS_GOOGLE_CONSUMER_KEY
    consumer_secret = settings.CONNECTED_ACCOUNTS_GOOGLE_CONSUMER_SECRET
    scope = settings.CONNECTED_ACCOUNTS_GOOGLE_SCOPE
    auth_params = settings.CONNECTED_ACCOUNTS_GOOGLE_AUTH_PARAMS


providers.register(GoogleProvider)
