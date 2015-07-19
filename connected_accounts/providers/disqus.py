import json
import logging

from django.utils.translation import ugettext_lazy as _
from requests import RequestException

from connected_accounts.conf import settings
from connected_accounts.provider_pool import providers

from .base import OAuth2Provider, ProviderAccount

logger = logging.getLogger('connected_accounts')


class DisqusAccount(ProviderAccount):

    def get_profile_url(self):
        return self.account.extra_data.get('profileUrl')

    def get_avatar_url(self):
        username = self.account.extra_data.get('username')
        return 'https://disqus.com/api/users/avatars/%s.jpg' % username  # noqa

    def to_str(self):
        default = super(DisqusAccount, self).to_str()
        return self.account.extra_data.get('name', default)

    def extract_common_fields(self):
        data = self.account.extra_data
        return dict(
            name=data.get('name', ''),
            email=data.get('email', ''),
            username=data.get('username', '')
        )


class DisqusProvider(OAuth2Provider):
    id = 'disqus'
    name = _('Disqus')
    account_class = DisqusAccount
    expires_in_key = 'expires_in'
    scope_separator = ','

    authorization_url = 'https://disqus.com/api/oauth/2.0/authorize/'
    access_token_url = 'https://disqus.com/api/oauth/2.0/access_token/'
    profile_url = 'https://disqus.com/api/3.0/users/details.json'

    consumer_key = settings.CONNECTED_ACCOUNTS_DISQUS_CONSUMER_KEY
    consumer_secret = settings.CONNECTED_ACCOUNTS_DISQUS_CONSUMER_SECRET
    scope = settings.CONNECTED_ACCOUNTS_DISQUS_SCOPE

    def get_profile_data(self, raw_token):
        """Fetch user profile information."""
        token_data = json.loads(raw_token)
        params = {
            'access_token': token_data['access_token'],
            'api_key': self.consumer_key,
            'api_secret': token_data['access_token']
        }
        try:
            response = self.request('get', self.profile_url, params=params)
            response.raise_for_status()
        except RequestException as e:
            logger.error('Unable to fetch user profile: {0}'.format(e))
            return None
        else:
            return response.json() or response.text

    def extract_uid(self, data):
        """Return unique identifier from the profile info."""
        return str(data['response']['id'])

    def extract_extra_data(self, data):
        return data.get('response', {})

providers.register(DisqusProvider)
