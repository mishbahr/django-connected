from django.db.models import ForeignKey


class AccountField(ForeignKey):

    def __init__(self, provider, **kwargs):
        if 'to' in kwargs:
            del(kwargs['to'])

        self.provider = provider
        kwargs.update({'limit_choices_to': {'provider': self.provider}})

        # We hard-code the `to` argument for ForeignKey.__init__
        # since a AccountField can only be a ForeignKey to a Account
        kwargs['to'] = 'connected_accounts.Account'
        super(AccountField, self).__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(AccountField, self).deconstruct()
        kwargs['provider'] = self.provider
        return name, path, args, kwargs

    def south_field_triple(self):
        """Returns a suitable description of this field for South."""
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = 'django.db.models.fields.related.ForeignKey'
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
