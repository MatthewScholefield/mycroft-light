from mycroft_core import MycroftSkill, Package, intent_handler


class SettingsSkill(MycroftSkill):
    @intent_handler('location')
    def location_handler(self, p: Package):
        p.data = {
            'city': self.rt.config['location']['city']['name']
        }
