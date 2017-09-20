from mycroft import MycroftSkill


class MathSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.register_intent('math', self.handle_math)
        self.register_entity('{num}')
        self.register_entity('{equation}')

    def handle_math(self, data):
        equation = data.matches.get('equation', data.query)
        answer, conf = self.parser.to_number(equation)
        self.add_result('equation', equation)
        self.add_result('answer', answer)
        return conf
