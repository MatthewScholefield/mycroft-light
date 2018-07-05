from glob import glob
from mycroft_core import MycroftSkill, Package, intent_handler
from psutil import Popen
from typing import Tuple, Iterator

from mycroft.skill_plugin import intent_prehandler
from mycroft.util.text import find_match


class DesktopLauncherSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.app_to_name = {i: j for i, j in self.find_apps()}
        self.name_to_app = {j: i for i, j in self.find_apps()}
        self.app_names = list(self.app_to_name) + list(self.name_to_app)

    @staticmethod
    def norm(s):
        return ''.join(c for c in s.strip() if c.isalpha() or c == ' ')

    def find_apps(self) -> Iterator[Tuple[str, str]]:
        for desktop_file in glob('/usr/share/applications/*.desktop'):
            app = name = ''
            with open(desktop_file) as f:
                for line in f:
                    if line.startswith('Exec='):
                        app = self.norm(line[len('Exec='):])
                    elif line.startswith('Name='):
                        name = self.norm(line[len('Name='):])
                    if name and app:
                        break
            if app and name:
                yield app, name

    @intent_prehandler('launch.app')
    def launch_app(self, p: Package):
        app, conf = find_match(p.data['app'], self.app_names)
        if conf < 0.6:
            return p.add(confidence=0.0)

        p.data = {
            'app': app
        }

    @launch_app.handler
    def launch_app(self, p: Package):
        Popen(self.name_to_app.get(p.data['app'], p.data['app']))
