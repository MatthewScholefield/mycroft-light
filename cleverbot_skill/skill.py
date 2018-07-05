from mycroft_core import MycroftSkill, Package, intent_handler, intent_prehandler


class CleverbotSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        raise NotImplementedError
        from cleverwrap import CleverWrap
        self.cl = CleverWrap(self.rt.remote_key.create_key('cleverbot.com', 'cleverbot'))

    @intent_prehandler('fallback', '')
    def fallback_prehandler(self, p: Package):
        return p.add(confidence=0.6)

    @intent_handler('fallback', '')
    def fallback(self, p: Package):
        p.speech = self.cl.say(p.match.query)
