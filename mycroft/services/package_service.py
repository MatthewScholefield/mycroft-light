from copy import deepcopy

from mycroft.package_cls import Package
from mycroft.services.service_plugin import ServicePlugin


class PackageService(ServicePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        self._package = Package()

    def add_struct(self, struct):
        """
        Register a data structure as part of the global package
        Example:
            >>> self.rt.package.add_struct({'album_art': {'url': str}})
            >>> def my_skill_handler(p: Package):
            ...     p.album_art.url = 'http://foo.com/bar.png'
        """
        self._package.add_struct(struct)

    def __setattr__(self, key, value):
        if key in ('config', 'rt') or key.startswith('_'):
            return object.__setattr__(self, key, value)
        return self._package.__setattr__(key, value)

    def __getattr__(self, item):
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            pass
        return self._package.__getattribute__(item)

    def __call__(self, **kwargs):
        """Get an empty package instance"""
        return deepcopy(self._package).add(**kwargs)
