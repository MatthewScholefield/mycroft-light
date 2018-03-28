from mycroft import MycroftSkill, intent_handler, Package


class QuitSkill(MycroftSkill):
    @intent_handler('quit')
    def hello(self):
        self.rt.main_thread.quit()
