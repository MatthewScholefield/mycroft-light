from mycroft_core import MycroftSkill, Package, intent_prehandler


class IntrospectionSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.rt.query.on_response(self.on_response)
        self.last_tts = self.last_skill = self.last_intent = ''

    def on_response(self, p: Package):
        self.last_tts = p.speech
        self.last_skill = p.skill
        self.last_intent = p.match.intent_id.split(':')[0]

    @intent_prehandler('what.skill.was.that')
    def handle_what_skill(self, p: Package):
        if not self.last_tts:
            return p.add(confidence=0.1)
        return p.add(data=dict(skill=self.last_skill, intent=self.last_intent))

