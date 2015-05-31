from django import forms
from django.contrib.admin.widgets import AdminRadioSelect
from django.utils.translation import ugettext_lazy as _

from .provider_pool import providers


class AccountCreationForm(forms.Form):
    provider = forms.ChoiceField(
        label=_('Provider'),
        choices=sorted(providers.as_choices(enabled_only=True), key=lambda provider: provider[1]),
        widget=AdminRadioSelect(attrs={'class': 'radiolist'}),
        error_messages={'required': _('Please select a provider.')})
