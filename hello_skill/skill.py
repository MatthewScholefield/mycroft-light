from mycroft import MycroftSkill, intent_handler, Package


class HelloSkill(MycroftSkill):
    @intent_handler('hello')
    def hello(self, p: Package):
        pass

    @intent_handler('bye')
    def bye(self, p: Package):
        pass

    @intent_handler('install')
    def install_skill(self, p: Package):
        p.action = 'what.skill.name'
        reply = self.get_response(p).query
        p.data['response'] = reply + ';;;;'
        p.action = 'you.just.said'

    @intent_handler('thanks')
    def thanks(self):
        pass
