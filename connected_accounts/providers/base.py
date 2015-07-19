from __future__ import unicode_literals

import json
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.crypto import constant_time_compare, get_random_string
from django.utils.encoding import force_text
from requests.api import request
from requests.exceptions import RequestException
from requests_oauthlib import OAuth1

try:
    from urllib.parse import urlencode, parse_qs
except ImportError:  # pragma: no cover
    # Python 2.X
    from urllib import urlencode
    from urlparse import parse_qs


logger = logging.getLogger('connected_accounts')


class ProviderAccount(object):
    def __init__(self, account, provider):
        self.account = account
        self.provider = provider

    def get_profile_url(self):
        return ''

    def get_avatar_url(self):
        return settings.STATIC_URL + 'img/connected_accounts/icon-user-default.jpg'

    def to_str(self):
        return self.provider.to_str()

    def extract_common_fields(self):
        return {}


class BaseOAuthProvider(object):
    id = ''
    name = ''
    account_class = ProviderAccount

    authorization_url = ''
    access_token_url = ''
    profile_url = ''

    consumer_key = ''
    consumer_secret = ''
    scope = []
    scope_separator = ' '


    def __init__(self, token=''):
        self.token = token

    def wrap_account(self, account):
        return self.account_class(account, self)

    def get_access_token(self, request, callback=None):
        """Fetch access token from callback request."""
        raise NotImplementedError('Defined in a sub-class')  # pragma: no cover

    def refresh_access_token(self, raw_token):
        """Refreshing an OAuth2 token using a refresh token."""
        raise NotImplementedError('Defined in a sub-class')  # pragma: no cover

    def get_profile_data(self, raw_token):
        """Fetch user profile information."""
        try:
            response = self.request('get', self.profile_url, token=raw_token)
            response.raise_for_status()
        except RequestException as e:
            logger.error('Unable to fetch user profile: {0}'.format(e))
            return None
        else:
            return response.json() or response.text

    def get_redirect_args(self, request, callback):
        """Get request parameters for redirect url."""
        raise NotImplementedError('Defined in a sub-class')  # pragma: no cover

    def get_redirect_url(self, request, callback, parameters=None):
        """Build authentication redirect url."""
        args = self.get_redirect_args(request, callback=callback)
        additional = parameters or {}
        args.update(additional)
        params = urlencode(args)
        return '{0}?{1}'.format(self.authorization_url, params)

    def parse_raw_token(self, raw_token):
        """Parse token and secret from raw token response."""
        raise NotImplementedError('Defined in a sub-class')  # pragma: no cover

    def request(self, method, url, **kwargs):
        """Build remote url request."""
        return request(method, url, **kwargs)

    def extract_uid(self, data):
        """Return unique identifier from the profile info."""
        return data.get('id', None)

    def get_scope(self, request):
        dynamic_scope = request.GET.get('scope', None)
        if dynamic_scope:
            self.scope.extend(dynamic_scope.split(','))
        return self.scope

    def extract_extra_data(self, data):
        return data

    @property
    def session_key(self):
        raise NotImplementedError('Defined in a sub-class')  # pragma: no cover

    @property
    def is_enabled(self):
        return self.consumer_key is not None and self.consumer_secret is not None

    def to_str(self):
        return force_text(self.name)


class OAuthProvider(BaseOAuthProvider):
    request_token_url = ''

    def get_access_token(self, request, callback=None):
        """Fetch access token from callback request."""
        raw_token = request.session.get(self.session_key, None)
        verifier = request.GET.get('oauth_verifier', None)
        if raw_token is not None and verifier is not None:
            data = {'oauth_verifier': verifier}
            callback = request.build_absolute_uri(callback or request.path)
            callback = force_text(callback)
            try:
                response = self.request(
                    'post', self.access_token_url,
                    token=raw_token, data=data, oauth_callback=callback)
                response.raise_for_status()
            except RequestException as e:
                logger.error('Unable to fetch access token: {0}'.format(e))
                return None
            else:
                return response.text
        return None

    def get_request_token(self, request, callback):
        """Fetch the OAuth request token. Only required for OAuth 1.0."""
        callback = force_text(request.build_absolute_uri(callback))
        try:
            response = self.request('post', self.request_token_url, oauth_callback=callback)
            response.raise_for_status()
        except RequestException as e:
            logger.error('Unable to fetch request token: {0}'.format(e))
            return None
        else:
            return response.text

    def get_redirect_args(self, request, callback):
        """Get request parameters for redirect url."""
        callback = force_text(request.build_absolute_uri(callback))
        raw_token = self.get_request_token(request, callback)
        token, secret, _ = self.parse_raw_token(raw_token)
        if token is not None and secret is not None:
            request.session[self.session_key] = raw_token
        args = {
            'oauth_token': token,
            'oauth_callback': callback,
        }

        scope = self.get_scope(request)
        if scope:
            args['scope'] = self.scope_separator.join(self.get_scope(request))

        return args

    def parse_raw_token(self, raw_token):
        """Parse token and secret from raw token response."""
        if raw_token is None:
            return (None, None, None)
        qs = parse_qs(raw_token)
        token = qs.get('oauth_token', [None])[0]
        token_secret = qs.get('oauth_token_secret', [None])[0]
        return (token, token_secret, None)

    def request(self, method, url, **kwargs):
        """Build remote url request. Constructs necessary auth."""
        user_token = kwargs.pop('token', self.token)
        token, secret, _ = self.parse_raw_token(user_token)
        callback = kwargs.pop('oauth_callback', None)
        verifier = kwargs.get('data', {}).pop('oauth_verifier', None)
        oauth = OAuth1(
            resource_owner_key=token,
            resource_owner_secret=secret,
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            verifier=verifier,
            callback_uri=callback,
        )
        kwargs['auth'] = oauth
        return super(OAuthProvider, self).request(method, url, **kwargs)

    @property
    def session_key(self):
        return 'connected-accounts-{0}-request-token'.format(self.id)


class OAuth2Provider(BaseOAuthProvider):
    supports_state = True
    expires_in_key = 'expires_in'
    auth_params = {}

    def check_application_state(self, request):
        """Check optional state parameter."""
        stored = request.session.get(self.session_key, None)
        returned = request.GET.get('state', None)
        check = False
        if stored is not None:
            if returned is not None:
                check = constant_time_compare(stored, returned)
            else:
                logger.error('No state parameter returned by the provider.')
        else:
            logger.error('No state stored in the sesssion.')
        return check

    def get_access_token(self, request, callback=None):
        """Fetch access token from callback request."""
        callback = request.build_absolute_uri(callback or request.path)
        if not self.check_application_state(request):
            logger.error('Application state check failed.')
            return None
        if 'code' in request.GET:
            args = {
                'client_id': self.consumer_key,
                'redirect_uri': callback,
                'client_secret': self.consumer_secret,
                'code': request.GET['code'],
                'grant_type': 'authorization_code',
            }
        else:
            logger.error('No code returned by the provider')
            return None
        try:
            response = self.request('post', self.access_token_url, data=args)
            response.raise_for_status()
        except RequestException as e:
            logger.error('Unable to fetch access token: {0}'.format(e))
            return None
        else:
            return response.text

    def refresh_access_token(self, raw_token, **kwargs):
        token, refresh_token, expires_at = self.parse_raw_token(raw_token)
        refresh_token = kwargs.pop('refresh_token', refresh_token)

        args = {
            'client_id': self.consumer_key,
            'client_secret': self.consumer_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        try:
            response = self.request('post', self.access_token_url, data=args)
            response.raise_for_status()
        except RequestException as e:
            logger.error('Unable to fetch access token: {0}'.format(e))
            return None
        else:
            return response.text

    def get_application_state(self, request, callback):
        """Generate state optional parameter."""
        return get_random_string(32)

    def get_auth_params(self, request, action=None):
        return self.auth_params

    def get_redirect_args(self, request, callback):
        """Get request parameters for redirect url."""
        callback = request.build_absolute_uri(callback)
        args = {
            'client_id': self.consumer_key,
            'redirect_uri': callback,
            'response_type': 'code',
        }

        scope = self.get_scope(request)
        if scope:
            args['scope'] = self.scope_separator.join(self.get_scope(request))

        state = self.get_application_state(request, callback)
        if state is not None:
            args['state'] = state
            request.session[self.session_key] = state

        auth_params = self.get_auth_params(request)
        if auth_params:
            args.update(auth_params)

        return args

    def parse_raw_token(self, raw_token):
        """Parse token and secret from raw token response."""
        if raw_token is None:
            return (None, None, None)
        # Load as json first then parse as query string
        try:
            token_data = json.loads(raw_token)
        except ValueError:
            qs = parse_qs(raw_token)
            token = qs.get('access_token', [None])[0]
            refresh_token = qs.get('refresh_token', [None])[0]
            expires_at = qs.get(self.expires_in_key, [None])[0]
        else:
            token = token_data.get('access_token', None)
            refresh_token = token_data.get('refresh_token', None)
            expires_at = token_data.get(self.expires_in_key, None)

        if expires_at:
            expires_at = timezone.now() + timedelta(seconds=int(expires_at))

        return (token, refresh_token, expires_at)

    def request(self, method, url, **kwargs):
        """Build remote url request. Constructs necessary auth."""
        user_token = kwargs.pop('token', self.token)
        token, secret, expires_at = self.parse_raw_token(user_token)
        if token is not None:
            params = kwargs.get('params', {})
            params['access_token'] = token
            kwargs['params'] = params
        return super(OAuth2Provider, self).request(method, url, **kwargs)

    @property
    def session_key(self):
        return 'connected-accounts-{0}-application-state'.format(self.id)
