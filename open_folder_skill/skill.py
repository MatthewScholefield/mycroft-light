from difflib import SequenceMatcher
from os.path import isdir, expanduser
from subprocess import call

from mycroft import MycroftSkill, MatchData


class OpenFolderSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.register_intent('open.path', self.open_path)
        self.register_intent('open.place', self.open_place)
        self.register_entity('place')
        self.register_entity('path')

    def open_path(self, data: MatchData):
        path = data.matches['path'].replace(' ', '')
        if not isdir(expanduser(path)):
            self.add_result('type', 'path')
            self.add_result('folder', path)
            self.set_action('not.found')
            return 0.5
        else:
            self.add_result('path', path)
            def callback():
                call(['xdg-open', path])
            self.set_callback(callback)
            return 0.9

    def open_place(self, data: MatchData):
        place = data.matches['place']

        if SequenceMatcher(a='home', b=place).ratio() > 0.5:
            folder = expanduser('~')
        elif 'skill' in place:
            folder = self.path_manager.skill_dir(place.lower().replace(' ', '_'))
        else:
            folder = ''

        if not isdir(folder):
            self.add_result('type', 'place')
            self.add_result('folder', place)
            self.set_action('not.found')
            return 0.6

        self.add_result('place', place)
        def callback():
            call(['xdg-open', folder])
        self.set_callback(callback)
        return 0.8
