from mycroft.api import DeviceApi
from mycroft.configuration import ConfigurationManager
from mycroft.mycroft_skill import ScheduledSkill


class ConfigurationSkill(ScheduledSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_delay(self.config.get('max_delay'))
        self.api = DeviceApi()
        self.config_hash = ''
        self.register_intent('update.config', self.handle_update)

    def handle_update(self, intent_data):
        if self.update():
            self.set_action('config.updated')
        else:
            self.set_action('config.no_change')

    def on_triggered(self):
        self.update()

    def update(self):
        config = self.api.find_setting()
        location = self.api.find_location()
        if location:
            config["location"] = location

        if self.config_hash != hash(str(config)):
            ConfigurationManager.load_defaults()
            self.config_hash = hash(str(config))
            return True
        else:
            return False
