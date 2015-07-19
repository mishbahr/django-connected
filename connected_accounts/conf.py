# -*- coding: utf-8 -*-

from appconf import AppConf
from django.conf import settings  # noqa


class ConnectedAccountsAppConf(AppConf):
    TWITTER_CONSUMER_KEY = None
    TWITTER_CONSUMER_SECRET = None

    FACEBOOK_CONSUMER_SECRET = None
    FACEBOOK_CONSUMER_KEY = None
    FACEBOOK_SCOPE = ['email', 'public_profile', 'user_friends']
    FACEBOOK_AUTH_PARAMS = {}

    GOOGLE_CONSUMER_SECRET = None
    GOOGLE_CONSUMER_KEY = None
    GOOGLE_SCOPE = ['https://www.googleapis.com/auth/plus.login', 'email']
    GOOGLE_AUTH_PARAMS = {
        'access_type': 'offline',
        'approval_prompt': 'force',
    }

    INSTAGRAM_CONSUMER_KEY = None
    INSTAGRAM_CONSUMER_SECRET = None
    INSTAGRAM_SCOPE = ['basic']

    BITLY_CONSUMER_KEY = None
    BITLY_CONSUMER_SECRET = None

    MAILCHIMP_CONSUMER_KEY = None
    MAILCHIMP_CONSUMER_SECRET = None

    DISQUS_CONSUMER_KEY = None
    DISQUS_CONSUMER_SECRET = None
    DISQUS_SCOPE = ['read', 'write', ]

    class Meta:
        prefix = 'connected_accounts'
