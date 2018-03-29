from shutil import which
from subprocess import call
from os.path import isfile, join

from mycroft.interfaces.tts.tts_plugin import TtsPlugin
from mycroft.util.git_repo import GitRepo


class MimicTts(TtsPlugin):
    def __init__(self, rt):
        super().__init__(rt)

        self.exe = which('mimic')
        self.exe = self.exe or self.download_mimic()

    def download_mimic(self):
        repo = GitRepo(self.rt.paths.mimic, self.config['url'], 'development', update_freq=24 * 7)
        if repo.try_pull():
            repo.run_inside('./dependencies.sh --prefix="/usr/local"')
            repo.run_inside('./autogen.sh')
            repo.run_inside('./configure --prefix=/usr/local')
            repo.run_inside('make -j2')
        return join(self.rt.paths.mimic_dir, 'mimic')

    def read(self, text):
        call([self.rt.paths.mimic_exe, '-t', text, '-voice', self.config['voice']])
