from mycroft.interfaces.speech.stt.stt_plugin import SttPlugin
from mycroft.plugin.base_plugin import BasePlugin
from mycroft.plugin.option_plugin import OptionMeta, OptionPlugin


class SttService(BasePlugin, OptionPlugin, metaclass=OptionMeta, base=SttPlugin,
                 package='mycroft.interfaces.speech.stt', suffix='_stt', default='mycroft'):
    _config = {
        'module': 'mycroft',
        'module.options': ['mycroft', 'google', 'ibm', 'wit']
    }

    def __init__(self, rt, plugin_base):
        self._plugin_path = plugin_base + '.stt'
        BasePlugin.__init__(self, rt)
        OptionPlugin.__init__(self, rt, __module__=self.config['module'])
