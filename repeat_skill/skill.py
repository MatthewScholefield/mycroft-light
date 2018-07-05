from mycroft_core import MycroftSkill, Package, intent_handler


class RepeatSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.stop_words = self.locale('stop.words.txt')

    @intent_handler('repeat')
    def handle_repeat(self, p: Package):
        p.speech = p.match.matches['text']

    @intent_handler('repeat.after.me')
    def handle_repeat_after_me(self, p: Package):
        response = self.get_response(p).query
        while not any(word in response for word in self.stop_words):
            response = self.get_response(self.package(speech=response)).query
        p.action = None
