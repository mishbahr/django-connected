import json
import logging

from django.utils.translation import ugettext_lazy as _
from requests.exceptions import RequestException

from connected_accounts.conf import settings
from connected_accounts.provider_pool import providers

from .base import OAuth2Provider, ProviderAccount

logger = logging.getLogger('connected_accounts')


class MailChimpAccount(ProviderAccount):
    def get_avatar_url(self):
        return settings.STATIC_URL + 'img/connected_accounts/providers/mailchimp.png'

    def to_str(self):
        default = super(MailChimpAccount, self).to_str()
        return self.account.extra_data.get('accountname', default)

    def get_token(self, token):
        """Returns oauth_token (OAuth1) or access token (OAuth2)"""
        return '{0}-{1}'.format(token, self.account.extra_data.get('dc', 'us1'))

    def extract_common_fields(self):
        data = self.account.extra_data
        return dict(name=data.get('accountname'))


class MailChimpProvider(OAuth2Provider):
    id = 'mailchimp'
    name = _('MailChimp')
    account_class = MailChimpAccount
    expires_in_key = ''

    authorization_url = 'https://login.mailchimp.com/oauth2/authorize'
    access_token_url = 'https://login.mailchimp.com/oauth2/token'
    profile_url = 'https://login.mailchimp.com/oauth2/metadata'

    consumer_key = settings.CONNECTED_ACCOUNTS_MAILCHIMP_CONSUMER_KEY
    consumer_secret = settings.CONNECTED_ACCOUNTS_MAILCHIMP_CONSUMER_SECRET

    def extract_uid(self, data):
        """Return unique identifier from the profile info."""
        return data.get('user_id', None)

    def get_profile_data(self, raw_token):
        """Fetch user profile information."""
        token_data = json.loads(raw_token)
        # This header is the 'magic' that makes this empty GET request work.
        headers = {'Authorization': 'OAuth %s' % token_data['access_token']}

        try:
            response = self.request('get', self.profile_url, headers=headers)
            response.raise_for_status()
        except RequestException as e:
            logger.error('Unable to fetch user profile: {0}'.format(e))
            return None
        else:
            return response.json() or response.text


providers.register(MailChimpProvider)
