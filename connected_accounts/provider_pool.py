from django.conf import settings

try:
    import importlib
except ImportError:
    from django.utils import importlib


class ProviderRegistry(object):
    def __init__(self):
        self.provider_map = {}
        self.discovered = False

    def get_list(self):
        self.discover_providers()
        return self.provider_map.values()

    def register(self, cls):
        self.provider_map[cls.id] = cls()

    def by_id(self, id):
        self.discover_providers()
        return self.provider_map.get(id)

    def as_choices(self, enabled_only=False):
        self.discover_providers()
        for provider in self.get_list():
            if not enabled_only or (enabled_only and provider.is_enabled):
                yield (provider.id, provider.name)

    def discover_providers(self):
        if not self.discovered:
            for app in settings.INSTALLED_APPS:
                provider_module = app + '.provider'
                try:
                    importlib.import_module(provider_module)
                except ImportError:
                    pass
            self.discovered = True

providers = ProviderRegistry()
