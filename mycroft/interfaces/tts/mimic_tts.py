from shutil import which
from subprocess import call

from mycroft.interfaces.tts.tts_plugin import TtsPlugin
from mycroft.util.git_repo import GitRepo


class MimicTts(TtsPlugin):
    _config = {
        'voice': 'ap',
        'voice.options': ['ap', 'slt', 'slt_hts', 'kal', 'awb', 'kal16', 'rms', 'awb_time'],
        'options': '',
        'url': 'https://github.com/MycroftAI/mimic.git'
    }
    _root_config = {
        'paths': {
            'mimic_dir': '${user_config}/mimic',
            'mimic_exe': '${mimic_dir}/mimic'
        }
    }

    def __init__(self, rt):
        super().__init__(rt)
        self.exe = which('mimic') or self.rt.paths.mimic_exe

    def setup(self):
        if which('mimic'):
            return
        repo = GitRepo(self.rt.paths.mimic, self.config['url'], 'development', update_freq=24 * 7)
        if repo.try_pull():
            repo.run_inside('./dependencies.sh --prefix="/usr/local"')
            repo.run_inside('./autogen.sh')
            repo.run_inside('./configure --prefix=/usr/local')
            repo.run_inside('make -j2')
        return self.rt.paths.mimic_exe

    def read(self, text):
        call([self.exe, '-t', text, '-voice', self.config['voice']])
