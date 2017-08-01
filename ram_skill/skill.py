import psutil

from mycroft.skill import MycroftSkill


class RamSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        for i in ['free',  'total']:
            self.register_intent('mem.' + i, self.create_handler(i))

    def format_kb(self, amount):
        gb = amount / (1024 * 1024 * 1024)
        if gb > 1.0:
            return round(gb, 1), 'GB', 'Gigabytes'
        else:
            return round(gb * 1024), 'MB', 'Megabytes'

    def create_handler(self, attribute):
        def callback():
            num, short, long = self.format_kb(getattr(psutil.virtual_memory(), attribute))
            self.add_result(attribute + '_short', str(num) + ' ' + short)
            self.add_result(attribute + '_long', str(num) + ' ' + long)
        return callback
