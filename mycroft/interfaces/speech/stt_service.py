from mycroft.base_plugin import BasePlugin
from mycroft.interfaces.speech.stt.stt_plugin import SttPlugin
from mycroft.option_plugin import OptionPlugin


class SttService(BasePlugin, OptionPlugin):
    def __init__(self, rt, plugin_base):
        self._plugin_path = plugin_base + '.stt'
        BasePlugin.__init__(self, rt)
        OptionPlugin.__init__(self, SttPlugin, 'mycroft.interfaces.speech.stt', '_stt', 'mycroft')
        self.init(self.config['module'], rt)
