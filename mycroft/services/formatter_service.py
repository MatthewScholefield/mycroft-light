from mycroft.formatters.formatter_plugin import FormatterPlugin
from mycroft.plugin.option_plugin import OptionPlugin, OptionMeta
from mycroft.services.service_plugin import ServicePlugin


class FormatterService(
    ServicePlugin, OptionPlugin, metaclass=OptionMeta, base=FormatterPlugin,
    package='mycroft.formatters', suffix='_formatter', default='en_us'
):
    def __init__(self, rt):
        ServicePlugin.__init__(self, rt)
        OptionPlugin.__init__(self, rt, __module__=rt.config['lang'].replace('-', '_'))
