from abc import ABCMeta

from mycroft.intent.intent_plugin import IntentPlugin


class FileIntentPlugin(IntentPlugin, metaclass=ABCMeta):
    pass
