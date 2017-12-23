from mycroft import MycroftSkill, MatchData


class StopSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.register_intent('stop', lambda: 0.4)
