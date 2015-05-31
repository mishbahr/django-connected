from functools import update_wrapper

from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from .fields import AccountField
from .forms import AccountCreationForm
from .models import Account
from .provider_pool import providers
from .views import OAuthCallback, OAuthRedirect
from .widgets import AccountRawIdWidget

try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl


try:
    from django.contrib.admin.utils import unquote
except ImportError:
    from django.contrib.admin.util import unquote


"""
Piggyback off admin.autodiscover() to discover providers
"""
providers.discover_providers()


PRESERVED_FILTERS_SESSION_KEY = '_preserved_filters'


class AccountAdmin(admin.ModelAdmin):
    actions = None
    change_form_template = 'admin/connected_accounts/account/change_form.html'
    readonly_fields = ('avatar', 'uid', 'provider', 'profile_url',
                       'oauth_token', 'oauth_token_secret', 'user',
                       'expires_at', 'date_added', 'last_login', )
    list_display = ('avatar', '__str__', 'provider', )
    list_display_links = ('__str__', )

    fieldsets = (
        (None, {
            'fields': ('avatar', 'provider', 'uid', 'profile_url', )
        }),
        (None, {
            'fields': ('oauth_token', 'oauth_token_secret', )
        }),
        (None, {
            'fields': ('date_added', 'last_login', 'expires_at', 'user', )
        }),
    )

    class Media:
        css = {
            'all': (
                'css/connected_accounts/admin/connected_accounts.css',
            )
        }

    def get_urls(self):
        """
        Add the export view to urls.
        """
        urls = super(AccountAdmin, self).get_urls()
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.opts.app_label, self.opts.model_name

        extra_urls = patterns(
            '',
            url(r'^login/(?P<provider>(\w|-)+)/$',
                wrap(OAuthRedirect.as_view()), name='%s_%s_login' % info),
            url(r'^callback/(?P<provider>(\w|-)+)/$',
                wrap(OAuthCallback.as_view()), name='%s_%s_callback' % info),
            url(r'^(.+)/json/$', wrap(self.json_view), name='%s_%s_json' % info),
        )
        return extra_urls + urls

    def add_view(self, request, form_url='', extra_context=None):
        if not self.has_add_permission(request):
            raise PermissionDenied

        data = None

        changelist_filters = request.GET.get('_changelist_filters')
        if request.method == 'GET' and changelist_filters is not None:
            changelist_filters = dict(parse_qsl(changelist_filters))
            if 'provider' in changelist_filters:
                data = {
                    'provider': changelist_filters['provider']
                }

        form = AccountCreationForm(data=request.POST if request.method == 'POST' else data)

        if form.is_valid():
            info = self.model._meta.app_label, self.model._meta.model_name
            preserved_filters = self.get_preserved_filters(request)
            request.session[PRESERVED_FILTERS_SESSION_KEY] = preserved_filters
            redirect_url = reverse('admin:%s_%s_login' % info,
                                   kwargs={'provider': form.cleaned_data['provider']})
            return redirect(redirect_url)

        fieldsets = (
            (None, {
                'fields': ('provider', )
            }),
        )

        adminForm = helpers.AdminForm(form, list(fieldsets), {}, model_admin=self)
        media = self.media + adminForm.media

        context = dict(
            adminform=adminForm,
            is_popup=IS_POPUP_VAR in request.GET,
            media=media,
            errors=helpers.AdminErrorList(form, ()),
            preserved_filters=self.get_preserved_filters(request),
        )

        context.update(extra_context or {})
        return self.render_change_form(request, context, add=True, change=False, form_url=form_url)

    def json_view(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))
        return HttpResponse(content=obj.to_json(),  content_type='application/json')

    def response_change(self, request, obj):
        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)
        msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj)}

        if '_reset_data' in request.POST:
            if obj.is_expired:
                obj.refresh_access_token()

            provider = obj.get_provider()
            profile_data = provider.get_profile_data(obj.raw_token)
            if profile_data is None:
                msg = _('Could not retrieve profile data for the %(name)s "%(obj)s" ') % msg_dict
                self.message_user(request, msg, messages.ERROR)
            else:
                obj.extra_data = provider.extract_extra_data(profile_data)
                obj.save()
                msg = _('The %(name)s "%(obj)s" was updated successfully.') % msg_dict
                self.message_user(request, msg, messages.SUCCESS)

            redirect_url = request.path
            redirect_url = add_preserved_filters(
                {'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        return super(AccountAdmin, self).response_change(request, obj)

    def avatar(self, obj):
        return render_to_string(
            'admin/connected_accounts/account/includes/changelist_avatar.html', {
                'avatar_url': obj.get_avatar_url(),
            })
    avatar.allow_tags = True
    avatar.short_description = _('Avatar')

    def profile_url(self, obj):
        if obj.get_profile_url():
            return '<a href="{0}" target="_blank">{0}</a>'.format(obj.get_profile_url())
        return '&mdash;'

    profile_url.allow_tags = True
    profile_url.short_description = _('Profile URL')


admin.site.register(Account, AccountAdmin)


class ConnectedAccountAdminMixin(object):

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        db = kwargs.get('using')
        if isinstance(db_field, AccountField):
            self.raw_id_fields = self.raw_id_fields + (db_field.name, )
            kwargs['widget'] = AccountRawIdWidget(
                db_field.rel, self.admin_site, using=db)
            return db_field.formfield(**kwargs)
        return super(ConnectedAccountAdminMixin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
