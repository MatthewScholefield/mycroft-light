from mycroft_core import MycroftSkill, Package, intent_handler


class GreetSkill(MycroftSkill):
    @intent_handler('greet')
    def greet(self):
        pass
