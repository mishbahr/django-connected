from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

try:
    from urllib.parse import urlencode
except ImportError:  # pragma: no cover
    # Python 2.X
    from urllib import urlencode


class AccountRawIdWidget(ForeignKeyRawIdWidget):
    """
    A Widget for displaying Providers in the "raw_id" interface rather than
    in a <select> box.
    """
    class Media:
        css = {
            'all': ('css/connected_accounts/admin/connected_accounts.css',)
        }
        js = ('js/connected_accounts/admin/widgets.js',)

    def render(self, name, value, attrs=None):
        rel_to = self.rel.to
        context = {}
        if attrs is None:
            attrs = {}

        attrs.update({
            'type': 'hidden',  # hide text input
            'class': 'vForeignKeyRawIdAdminField vAccountRawIdWidget',  # The JavaScript code looks for this hook.
        })

        rel_to_info = rel_to._meta.app_label, rel_to._meta.model_name
        related_url = reverse(
            'admin:%s_%s_changelist' % rel_to_info, current_app=self.admin_site.name)

        params = self.url_parameters()
        if params:
            querystring = '?' + urlencode(params)
        else:
            querystring = ''

        hidden_input = super(ForeignKeyRawIdWidget, self).render(name, value, attrs)

        context.update({
            'lookup_name': name,
            'hidden_input': hidden_input,
            'ajax_url': reverse('admin:%s_%s_json' % rel_to_info, args=('_id_',)),
            'lookup_url': '%s%s' % (related_url, querystring),
            'related_obj': self.get_object(value),

        })

        html = render_to_string('admin/connected_accounts/account/widgets/account_widget.html', context)
        return mark_safe(html)

    def get_object(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.get(**{key: value})
        except (ValueError, self.rel.to.DoesNotExist):
            obj = None
        return obj
