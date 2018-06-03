from mycroft.intent.file_intents.file_intent_plugin import FileIntentPlugin
from mycroft.intent.intent_plugin import IntentPlugin
from mycroft.plugin.option_plugin import OptionMeta, OptionPlugin


class FileIntent(IntentPlugin, OptionPlugin, metaclass=OptionMeta, base=FileIntentPlugin,
                 package='mycroft.intent.file_intents', suffix='_file_intent', default='padaos'):
    _config = {'module': 'padaos'}

    def __init__(self, rt):
        IntentPlugin.__init__(self, rt)
        OptionPlugin.__init__(self, rt, __module__=self.config['module'])
