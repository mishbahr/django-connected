from __future__ import unicode_literals

import logging

from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, View

from .models import Account
from .provider_pool import providers

logger = logging.getLogger('connected_accounts')


class OAuthProvidertMixin(object):
    """Mixin for getting OAuth client for a provider."""

    provider = None

    def get_provider(self, provider):
        """Get instance of the OAuth client for this provider."""
        if self.provider is not None:
            return self.provider
        return providers.by_id(provider)


class OAuthRedirect(OAuthProvidertMixin, RedirectView):
    """Redirect user to OAuth provider to enable access."""

    model = Account
    permanent = False

    def get_additional_parameters(self, provider):
        """Return additional redirect parameters for this provider."""
        return {}

    def get_callback_url(self, provider):
        """Return the callback url for this provider."""
        info = self.model._meta.app_label, self.model._meta.model_name
        return reverse('admin:%s_%s_callback' % info, kwargs={'provider': provider.id})

    def get_redirect_url(self, **kwargs):
        """Build redirect url for a given provider."""
        provider_id = kwargs.get('provider', '')
        provider = self.get_provider(provider_id)
        if not provider:
            raise Http404('Unknown OAuth provider.')
        callback = self.get_callback_url(provider)
        params = self.get_additional_parameters(provider)
        return provider.get_redirect_url(self.request, callback=callback, parameters=params)


class OAuthCallback(OAuthProvidertMixin, View):
    """Base OAuth callback view."""
    model = Account

    def get(self, request, *args, **kwargs):
        name = kwargs.get('provider', '')
        provider = self.get_provider(name)
        if not provider:
            raise Http404('Unknown OAuth provider.')

        callback = self.get_callback_url(provider)
        # Fetch access token
        raw_token = provider.get_access_token(self.request, callback=callback)
        if raw_token is None:
            return self.handle_login_failure(provider, 'Could not retrieve token.')

        # Fetch profile info
        profile_data = provider.get_profile_data(raw_token)

        if profile_data is None:
            return self.handle_login_failure(provider, 'Could not retrieve profile.')

        identifier = provider.extract_uid(profile_data)
        if identifier is None:
            return self.handle_login_failure(provider, 'Could not determine uid.')

        token, token_secret, expires_at = provider.parse_raw_token(raw_token)

        account_defaults = {
            'raw_token': raw_token,
            'oauth_token': token,
            'oauth_token_secret': token_secret,
            'user': self.request.user,
            'extra_data': provider.extract_extra_data(profile_data),
            'expires_at': expires_at,
        }

        account, created = Account.objects.get_or_create(
            provider=provider.id, uid=identifier, defaults=account_defaults
        )

        opts = account._meta
        msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(account)}

        if created:
            msg = _('The %(name)s "%(obj)s" was added successfully.') % msg_dict
            messages.add_message(request, messages.SUCCESS, msg)
        else:
            for (key, value) in account_defaults.iteritems():
                setattr(account, key, value)
            account.save()

            msg = _('The %(name)s "%(obj)s" was updated successfully.') % msg_dict
            messages.add_message(request, messages.SUCCESS, msg)

        return redirect(self.get_login_redirect(provider, account))

    def get_callback_url(self, provider):
        """Return callback url if different than the current url."""
        return None

    def get_login_redirect(self, provider, account):
        """Return url to redirect authenticated users."""
        info = self.model._meta.app_label, self.model._meta.model_name
        # inline import to prevent circular imports.
        from .admin import PRESERVED_FILTERS_SESSION_KEY
        preserved_filters = self.request.session.get(PRESERVED_FILTERS_SESSION_KEY, None)
        redirect_url = reverse('admin:%s_%s_changelist' % info)
        if preserved_filters:
            redirect_url = add_preserved_filters(
                {'preserved_filters': preserved_filters, 'opts': self.model._meta}, redirect_url)
        return redirect_url

    def get_error_redirect(self, provider, reason):
        """Return url to redirect on login failure."""
        info = self.model._meta.app_label, self.model._meta.model_name
        return reverse('admin:%s_%s_changelist' % info)

    def handle_login_failure(self, provider, reason):
        """Message user and redirect on error."""
        logger.error('Authenication Failure: {0}'.format(reason))
        messages.error(self.request, 'Authenication Failed. Please try again')
        return redirect(self.get_error_redirect(provider, reason))
