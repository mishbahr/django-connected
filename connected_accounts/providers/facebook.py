from django.utils.translation import ugettext_lazy as _

from connected_accounts.conf import settings
from connected_accounts.provider_pool import providers

from .base import OAuth2Provider, ProviderAccount


class FacebookAccount(ProviderAccount):

    def get_profile_url(self):
        return self.account.extra_data.get('link')

    def get_avatar_url(self):
        uid = self.account.uid
        # ask for a 600x600 pixel image. We might get smaller but
        # image will always be highest res possible and square
        return 'https://graph.facebook.com/v2.3/%s/picture' \
               '?type=square&height=600&width=600&return_ssl_resources=1' % uid  # noqa

    def to_str(self):
        default = super(FacebookAccount, self).to_str()
        return self.account.extra_data.get('name', default)

    def extract_common_fields(self):
        data = self.account.extra_data
        return dict(email=data.get('email'),
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'))


class FacebookProvider(OAuth2Provider):
    id = 'facebook'
    name = _('Facebook')
    account_class = FacebookAccount
    expires_in_key = 'expires'

    authorization_url = 'https://www.facebook.com/dialog/oauth'
    access_token_url = 'https://graph.facebook.com/oauth/access_token'
    profile_url = 'https://graph.facebook.com/me'

    consumer_key = settings.CONNECTED_ACCOUNTS_FACEBOOK_CONSUMER_KEY
    consumer_secret = settings.CONNECTED_ACCOUNTS_FACEBOOK_CONSUMER_SECRET
    scope = settings.CONNECTED_ACCOUNTS_FACEBOOK_SCOPE
    auth_params = settings.CONNECTED_ACCOUNTS_FACEBOOK_AUTH_PARAMS

providers.register(FacebookProvider)
