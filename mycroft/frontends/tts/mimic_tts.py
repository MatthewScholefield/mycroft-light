from subprocess import call

from mycroft.frontends.tts.tts_plugin import TtsPlugin


class MimicTts(TtsPlugin):
    def read(self, text):
        call(['mimic', '-t', text, '-voice', self.config['voice']])
