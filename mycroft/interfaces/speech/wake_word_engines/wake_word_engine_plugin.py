from abc import abstractmethod
from typing import Callable

from mycroft.base_plugin import BasePlugin


class WakeWordEnginePlugin(BasePlugin):
    """Engine that runs self.on_activation() when it hears a wake word"""
    def __init__(self, rt, on_activation: Callable):
        super().__init__(rt)
        self.on_activation = on_activation
        speech_config = rt.config['interfaces']['speech']
        self.wake_word = speech_config['wake_word_engine']['wake_word'].replace(' ', '-')
        self.rec_config = speech_config['recognizer']
        self.config = speech_config['wake_word_engine'].get(self._attr_name)

    @abstractmethod
    def startup(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def continue_listening(self):
        pass

    @abstractmethod
    def pause_listening(self):
        pass

    def update(self, audio_buffer: bytes):
        pass
