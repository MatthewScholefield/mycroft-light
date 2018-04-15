from datetime import datetime

from mycroft_core import MycroftSkill, Package, intent_prehandler


class TimeSkill(MycroftSkill):
    @intent_prehandler('time')
    def time(self, p: Package):
        p.data['time'] = datetime.now().strftime("%H:%M")
