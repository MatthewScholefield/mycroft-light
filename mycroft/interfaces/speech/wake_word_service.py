from typing import Callable

from mycroft.plugin.base_plugin import BasePlugin
from mycroft.interfaces.speech.wake_word_engines.wake_word_engine_plugin import WakeWordEnginePlugin
from mycroft.plugin.option_plugin import OptionMeta, OptionPlugin


class WakeWordService(
    BasePlugin, OptionPlugin, metaclass=OptionMeta, base=WakeWordEnginePlugin,
    package='mycroft.interfaces.speech.wake_word_engines', suffix='_engine', default='pocketsphinx'
):
    def __init__(self, rt, on_activation: Callable):
        self._plugin_path = 'interfaces.speech.wake_word_engine'
        BasePlugin.__init__(self, rt)
        OptionPlugin.__init__(self, rt, on_activation=on_activation,
                              __module__=self.config['module'])
