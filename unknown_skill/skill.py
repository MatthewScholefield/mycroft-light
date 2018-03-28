from mycroft import MycroftSkill, intent_handler, Package


class UnknownSkill(MycroftSkill):
    def __init__(self):
        super().__init__()

    @intent_handler('fallback', '')
    def fallback(self, p: Package):
        pass
