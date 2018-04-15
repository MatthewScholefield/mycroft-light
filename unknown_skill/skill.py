from mycroft_core import MycroftSkill, intent_handler, Package, intent_prehandler


class UnknownSkill(MycroftSkill):
    def __init__(self):
        super().__init__()

    @intent_prehandler('fallback', '')
    def fallback(self, p: Package):
        return p.add(confidence=0.5)
