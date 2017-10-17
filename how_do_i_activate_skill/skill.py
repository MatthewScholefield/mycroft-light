import os
from glob import glob
from os.path import join, basename

from mycroft import MycroftSkill, MatchData


class HowDoIActivateSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.register_intent('how.do.i.activate', self.show_intent)
        self.register_entity('skill')

    def show_intent(self, data: MatchData):
        skill = data.matches['skill'].title().replace(' ', '')
        self.add_result('skill', skill)

        skill_dir = self.path_manager.dialog_dir(skill)
        if not os.path.isdir(skill_dir):
            self.set_action('skill.not.found')
            return 0.6

        intent_data = '\n'
        for fn in glob(join(skill_dir, '*.intent')):
            with open(fn) as f:
                intent_data += f.read()
        self.add_result('intent_data', intent_data)
