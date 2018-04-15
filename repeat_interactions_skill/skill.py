from mycroft_core import MycroftSkill, Package, intent_handler


class RepeatInteractionsSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.last_stts = []
        self.last_ttss = []
        self.rt.query.on_query(self.on_query)
        self.rt.query.on_response(self.on_response)
        self.owns_response = False

    def shutdown(self):
        self.rt.query.remove_on_query(self.on_query)
        self.rt.query.remove_on_response(self.on_response)

    def on_query(self, query):
        if query:
            self.last_stts.append(query)

    def on_response(self, p: Package):
        if self.owns_response:
            self.owns_response = False
            return
        self.last_ttss.append(p.speech)

    def on_handler(self):
        if len(self.last_stts) > 0:
            self.last_stts.pop(-1)
        self.owns_response = True

    @intent_handler('what.did.i.say')
    def what_did_i_say(self, p: Package):
        self.on_handler()
        p.data.update({
            'text': self.last_stts[-1] if len(self.last_stts) > 0 else 'nothing'
        })

    @intent_handler('before.that')
    def before_that(self, p: Package):
        self.on_handler()
        self.what_did_i_say(p)

    @intent_handler('what.did.you.say')
    def what_did_you_say(self, p: Package):
        self.on_handler()
        p.data.update({
            'text': self.last_stts[-1]
        })
