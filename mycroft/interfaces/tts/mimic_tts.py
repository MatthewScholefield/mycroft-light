from subprocess import call
from os.path import isfile

from mycroft.interfaces.tts.tts_plugin import TtsPlugin
from mycroft.util.git_repo import GitRepo


class MimicTts(TtsPlugin):
    def __init__(self, rt):
        super().__init__(rt)

        if not isfile(self.rt.paths.mimic_exe):
            self.download_mimic()

    def download_mimic(self):
        repo = GitRepo(self.rt.paths.mimic, self.config['url'], 'development')
        repo.try_pull()
        repo.run_inside('./dependencies.sh --prefix="/usr/local"')
        repo.run_inside('./autogen.sh')
        repo.run_inside('./configure --prefix=/usr/local')
        repo.run_inside('make -j2')

    def read(self, text):
        call([self.rt.paths.mimic_exe, '-t', text, '-voice', self.config['voice']])
