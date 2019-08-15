from time import sleep

import os
from threading import Thread

from mycroft_core import MycroftSkill, intent_handler


class QuitSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        if self.rt.config['platform']['mode'] != 'cli':
            raise NotImplementedError

    @intent_handler('quit')
    def hello(self):
        self.rt.main_thread.quit()
        Thread(target=self.delay_force_quit, daemon=True).start()

    def delay_force_quit(self):
        sleep(1)
        os._exit(0)
