from mycroft import MycroftSkill, MatchData


class TestingSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.register_intent('activate', self.acztivate)

    def activate(self, data: MatchData):
        self.add_result('', None)
