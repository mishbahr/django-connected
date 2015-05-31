from django.utils.translation import ugettext_lazy as _

from connected_accounts.conf import settings
from connected_accounts.provider_pool import providers

from .base import OAuthProvider, ProviderAccount


class TwitterAccount(ProviderAccount):
    def get_screen_name(self):
        return self.account.extra_data.get('screen_name')

    def get_profile_url(self):
        profile_url = None
        screen_name = self.get_screen_name()
        if screen_name:
            profile_url = 'http://twitter.com/' + screen_name
        return profile_url

    def get_avatar_url(self):
        avatar_url = None
        profile_image_url = self.account.extra_data.get('profile_image_url')
        if profile_image_url:
            # Hmm, hack to get our hands on the large image.  Not
            # really documented, but seems to work.
            avatar_url = profile_image_url.replace('_normal', '')
        return avatar_url

    def to_str(self):
        screen_name = self.get_screen_name()
        return '@%s' % screen_name if screen_name else super(TwitterAccount, self).to_str()

    def extract_common_fields(self):
        data = self.account.extra_data
        return dict(username=data.get('screen_name'),
                    name=data.get('name'))


class TwitterProvider(OAuthProvider):
    id = 'twitter'
    name = _('Twitter')
    account_class = TwitterAccount

    authorization_url = 'https://api.twitter.com/oauth/authenticate'
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    profile_url = 'https://api.twitter.com/1.1/account/verify_credentials.json'

    consumer_key = settings.CONNECTED_ACCOUNTS_TWITTER_CONSUMER_KEY
    consumer_secret = settings.CONNECTED_ACCOUNTS_TWITTER_CONSUMER_SECRET

providers.register(TwitterProvider)
