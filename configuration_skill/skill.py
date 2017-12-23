import json

from mycroft.skills.skill_plugin import ScheduledSkill
from mycroft.api import DeviceApi


class ConfigurationSkill(ScheduledSkill):
    def __init__(self):
        super().__init__()
        self.set_delay(self.config.get('max_delay'))
        self.api = DeviceApi(self.rt)
        self.config_hash = ''
        self.register_intent('update.config', self.update)

    def on_triggered(self):
        self.update()

    def update(self):
        if not self.rt.device_info:
            return
        settings = DeviceApi(self.rt).get_settings()
        new_hash = hash(json.dumps(settings, sort_keys=True))
        if self.config_hash != new_hash:
            def callback():
                self.rt.config.load_remote(settings)
                self.config_hash = new_hash
            self.set_callback(callback)
            self.set_action('config.updated')
        else:
            self.set_action('config.no_change')
