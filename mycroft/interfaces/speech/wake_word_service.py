from typing import Callable

from mycroft.base_plugin import BasePlugin
from mycroft.interfaces.speech.wake_word_engines.wake_word_engine_plugin import WakeWordEnginePlugin
from mycroft.option_plugin import OptionPlugin


class WakeWordService(BasePlugin, OptionPlugin):
    def __init__(self, rt, on_activation: Callable):
        self._plugin_path = 'interfaces.speech.wake_word_engine'
        BasePlugin.__init__(self, rt)
        OptionPlugin.__init__(self, WakeWordEnginePlugin, 'mycroft.interfaces.speech.wake_word_engines',
                              '_engine', 'pocketsphinx')
        self.init(self.config['module'], rt, on_activation=on_activation)
