from mycroft.plugin.base_plugin import BasePlugin
from mycroft.plugin.option_plugin import MustOverride


class TtsPlugin(BasePlugin):
    def read(self, text):
        raise MustOverride
