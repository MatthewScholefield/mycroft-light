from importlib import import_module
from inspect import isclass

from mycroft.util import log
from mycroft.util.text import to_camel, to_snake


def load_class(package: str, suffix: str, module: str, plugin_path: str, attr_name: str = None):
    package = package + '.' + module + suffix
    log.debug('Loading {}{}...'.format(module, suffix))
    try:
        mod = import_module(package)
        cls_name = to_camel(module + suffix)
        cls = getattr(mod, cls_name, '')
        if not isclass(cls):
            log.error('Could not find', cls_name, 'in', package)
        else:
            plugin_path += '.' if plugin_path else ''
            cls._attr_name = to_snake(cls.__name__).replace(suffix, '')
            cls._plugin_path = plugin_path + (attr_name or cls._attr_name)
            return cls
    except Exception:
        log.exception('Loading Module', package)
    return None


def load_plugin(plugin_cls, args, kwargs):
    if not plugin_cls:
        return None
    try:
        return plugin_cls(*args, **kwargs)
    except Exception:
        log.exception('Loading', plugin_cls.__name__)
    return None


class Empty:
    """Empty class used as placeholder when format not installed"""

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False

    def __getitem__(self, item):
        return self