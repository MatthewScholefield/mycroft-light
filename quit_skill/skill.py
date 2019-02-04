from mycroft_core import MycroftSkill, intent_handler


class QuitSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        if self.rt.config['platform']['mode'] != 'cli':
            raise NotImplementedError

    @intent_handler('quit')
    def hello(self):
        self.rt.main_thread.quit()
