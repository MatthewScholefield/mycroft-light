from alsaaudio import Mixer

from mycroft import MycroftSkill, MatchData
from mycroft.util import log
from mycroft.util.audio import play_audio
from os.path import join


class VolumeSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.min = self.config['min']
        self.max = self.config['max']
        self.steps = self.config['steps']
        self.change_volume_wav = join(self.rt.paths.audio, 'change_volume.wav')
        self.prev_volume = None

        self.register_intent('mute.volume', self.handle_mute)
        self.register_intent('unmute.volume', self.handle_unmute)
        self.register_intent('check.volume', self.handle_check_volume)
        self.register_intent('increase.volume', lambda: self.set_callback(self.increase_volume))
        self.register_intent('decrease.volume', lambda: self.set_callback(self.decrease_volume))
        self.register_intent('set.volume', self.handle_set_volume)
        self.register_entity('level')

    def get_level(self):
        return self.steps * (Mixer().getvolume()[0] - self.min) / (self.max - self.min)

    def change_volume(self, change):
        self.set_volume(self.get_level() + change)

    def set_volume(self, volume):
        volume = min(max(volume, 0), self.steps)
        Mixer().setvolume(round(100 * volume / self.steps))
        self.rt.formats.faceplate.command('eyes.volume=' + str(round(volume)))
        play_audio(self.change_volume_wav)

    def increase_volume(self):
        self.change_volume(+1)

    def decrease_volume(self):
        self.change_volume(-1)

    def handle_set_volume(self, data: MatchData):
        try:
            level = float(data['level'])

            def callback():
                self.set_volume(level)
            self.set_callback(callback)
            return 0.8
        except (KeyError, ValueError):
            log.exception('Parsing Level')
            self.add_result('min', 0)
            self.add_result('max', self.steps)
            self.set_action('invalid.volume')
            return 0.6

    def handle_check_volume(self):
        self.add_result('volume', self.get_level())

    def handle_mute(self):
        self.prev_volume = self.get_level()
        self.set_callback(lambda: self.set_volume(0))
        return 0.8 if self.get_level() != 0 else 0.6

    def handle_unmute(self):
        if self.get_level() == 0:
            self.set_callback(lambda: self.set_volume(self.prev_volume))
            return 0.8
        return 0.5
