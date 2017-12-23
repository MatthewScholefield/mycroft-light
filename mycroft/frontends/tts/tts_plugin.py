from abc import abstractmethod

from mycroft.base_plugin import BasePlugin


class TtsPlugin(BasePlugin):
    @abstractmethod
    def read(self, text):
        pass
