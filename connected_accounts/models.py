# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from .conf import settings
from .provider_pool import providers

logger = logging.getLogger('connected_accounts')


@python_2_unicode_compatible
class Account(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('User'), editable=False)
    provider = models.CharField(
        verbose_name=_('Provider'), max_length=50,
        choices=providers.as_choices())

    uid = models.CharField(verbose_name=_('UID'), max_length=255)
    last_login = models.DateTimeField(
        verbose_name=_('Last login'), auto_now=True)
    date_added = models.DateTimeField(
        verbose_name=_('Date added'), auto_now_add=True)
    raw_token = models.TextField(editable=False)
    oauth_token = models.TextField(
        verbose_name=_('OAuth Token'),
        help_text=_('"oauth_token" (OAuth1) or access token (OAuth2)'))
    oauth_token_secret = models.TextField(
        verbose_name=_('OAuth Token Secret'), blank=True, null=True,
        help_text=_('"oauth_token_secret" (OAuth1) or refresh token (OAuth2)'))

    extra_data = JSONField(verbose_name=_('Extra data'), editable=False)
    expires_at = models.DateTimeField(_('Expires at'), blank=True, null=True)

    def __str__(self):
        return self.get_provider_account().to_str()

    class Meta:
        ordering = ('-last_login', )

    @property
    def is_expired(self):
        now = timezone.now()
        if self.expires_at and now >= self.expires_at:
            return True
        return False

    def get_profile_url(self):
        return self.get_provider_account().get_profile_url()

    def get_avatar_url(self):
        return self.get_provider_account().get_avatar_url()

    def get_provider(self):
        if not hasattr(self, '_provider'):
            self._provider = providers.by_id(self.provider)
        return self._provider

    def get_provider_account(self):
        if not hasattr(self, '_provider_account'):
            self._provider_account = self.get_provider().wrap_account(self)
        return self._provider_account

    def refresh_access_token(self):
        """Refreshing an OAuth2 access token using refresh_token."""
        raw_token = self.get_provider().refresh_access_token(
            self.raw_token, refresh_token=self.oauth_token_secret)
        if raw_token is None:
            logger.error('Unable to refresh access token')
            return False

        self.raw_token = raw_token
        self.oauth_token, _, self.expires_at = \
            self.get_provider().parse_raw_token(raw_token)
        self.save(update_fields=('raw_token', 'oauth_token', 'expires_at', ))

    def get_token(self):
        """Returns oauth_token (OAuth1) or access token (OAuth2)"""
        if self.is_expired:
            self.refresh_access_token()

        get_token = getattr(self.get_provider_account(), 'get_token', None)
        if callable(get_token):  # special case for MailChimp
            return get_token(self.oauth_token)

        return self.oauth_token or None

    def get_token_secret(self):
        """ Returns oauth_token_secret (OAuth1) or refresh_token (OAuth2)"""
        return self.oauth_token_secret or None

    def get_common_data(self):
        data = {
            'provider_name': self.get_provider().to_str(),
            'account': self.get_provider_account().to_str(),
            'uid': self.uid,
            'oauth_token': self.get_token(),
            'outh_token_secret': self.get_token_secret(),
            'profile_url': self.get_profile_url(),
            'avatar_url': self.get_avatar_url(),
        }
        data.update(self.get_provider_account().extract_common_fields())
        return data

    def to_json(self):
        return json.dumps(self.get_common_data(), cls=DjangoJSONEncoder)
