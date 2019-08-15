from enum import Enum, unique
from inspect import signature, isclass

from mycroft.plugin.base_plugin import BasePlugin
from mycroft.util import log


@unique
class Format(Enum):
    speech = 1
    text = 2


class FormatterPlugin(BasePlugin):
    and_ = 'and'

    def __init__(self, rt):
        super().__init__(rt)
        self.formatters = {
            str: str,
            int: str,
            float: lambda x: '{:.2f}'.format(x),
            list: self.format_list
        }

    def format_list(self, obj, fmt):
        if len(obj) == 0:
            return ''
        if len(obj) == 1:
            return self.format(obj[0], fmt)
        return '{}, {} {}'.format(
            ', '.join(self.format(i, fmt) for i in obj[:-1]), self.and_,
            self.format(obj[-1], fmt)
        )

    def add(self, cls, formatter):
        self.formatters[cls] = formatter

    def format(self, obj, fmt=Format.speech):
        handler = self.formatters.get(type(obj))
        if not handler:
            log.warning('No formatter for', type(obj))
            return str(obj)
        if isclass(handler) or len(signature(handler).parameters) == 1:
            return handler(obj)
        else:
            return handler(obj, fmt)
