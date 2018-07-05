from time import monotonic

import random
from mycroft_core import MycroftSkill, Package, intent_prehandler, intent_handler

from mycroft.util import log


class DialogSelector:
    def __init__(self, conversations):
        self.conversations = conversations

    @staticmethod
    def normalize(sentence):
        return ''.join(c for c in sentence if c.isalpha() or c == ' ').lower().strip()

    @classmethod
    def normalize_conv(cls, conv):
        return list(map(cls.normalize, conv))

    def select_response(self, history):
        best_count = 1
        best_responses = []
        for conv in self.conversations:
            for conv_end in range(1, len(conv)):
                test_conv = conv[:conv_end]
                test_history = history[-len(test_conv):]
                if self.normalize_conv(test_conv) == self.normalize_conv(test_history):
                    same_count = len(test_conv)
                    if same_count == best_count:
                        best_responses.append(conv[conv_end])
                    elif same_count > best_count:
                        best_count = same_count
                        best_responses = [conv[conv_end]]
        if not best_responses:
            return None
        return random.choice(best_responses)

    def add_conversation(self, history):
        for conv_id, conv in enumerate(self.conversations):
            if len(history) >= len(conv):
                for a, b in zip(conv, history):
                    if self.normalize(a) != self.normalize(b):
                        break
                else:
                    self.conversations[conv_id] = history
                    break
        else:
            self.conversations.append(history)


class DialogSkill(MycroftSkill):
    interaction_threshold = 30

    def __init__(self):
        super().__init__()
        self.just_responded = False
        self.last_interaction_time = monotonic()
        self.current_interaction = []
        self.last_question = ''

        self.coded = self.filesystem.read('locale', self.lang, 'coded_responses.json').list()
        conversations = self.filesystem.read('responses.json').list() or self.coded
        self.dialog_selector = DialogSelector(conversations)

        self.rt.query.on_query(self.on_query)
        self.learn_intents = self.intent_context(['unsure', 'learn.response'])

    def shutdown(self):
        log.info('Shutting down dialog...')
        self.interaction_threshold = 0
        self.update_interaction()
        self.filesystem.write('responses.json').list(self.dialog_selector.conversations)
        self.rt.query.remove_on_query(self.on_query)

    def on_query(self, query):
        if not self.just_responded:
            self.last_interaction_time = 0
        self.just_responded = False

    def interaction_expired(self) -> bool:
        return monotonic() - self.last_interaction_time > self.interaction_threshold

    def end_interaction(self):
        self.dialog_selector.add_conversation(self.current_interaction)
        self.current_interaction = []

    def update_interaction(self):
        if self.interaction_expired():
            if self.current_interaction:
                self.end_interaction()
            self.last_question = ''

    @intent_prehandler('can.i.teach.you')
    def can_i_teach_you(self, p: Package):
        if not self.last_question:
            return p.add(confidence=0.6, action='no.recent.question')

    @intent_handler('can.i.teach.you')
    def can_i_teach_you_handler(self, p: Package):
        if p.action == 'no.recent.question':
            return p
        data = self.get_response(
            self.package(
                action='sure.how.to.respond',
                data={'question': self.last_question}
            ),
            self.learn_intents
        )
        if data.intent_id == 'learn.response':
            self.current_interaction = [self.last_question]
            self.current_interaction.append(data.matches['response'])
            self.end_interaction()
            return p.add(action='thanks.for.teaching')
        else:
            return p.add(action='ignore.learn')

    @intent_handler('what.have.i.taught.you')
    def what_have_i_taught_you(self, p: Package):
        p.data = {'count': len(self.dialog_selector.conversations) - len(self.coded)}

    @intent_prehandler('fallback', '')
    def fallback(self, p: Package) -> Package:
        self.update_interaction()
        if not p.match.query:
            return p.add(confidence=0.0)
        resp = self.dialog_selector.select_response(self.current_interaction + [p.match.query])

        if resp:
            self.just_responded = True
            self.last_interaction_time = monotonic()
            self.current_interaction.append(p.match.query)
            self.current_interaction.append(resp)
            return p.add(confidence=0.8, speech=resp)

        self.just_responded = False
        self.last_question = p.match.query

        return p.add(confidence=0.6 if random.random() > 0.9 else 0.0)

    @intent_handler('fallback', '')
    def fallback_handler(self, p: Package):
        if p.speech:
            return p

        self.just_responded = True
        data = self.get_response(self.package(action='learn'), self.learn_intents)
        if data.intent_id == 'learn.response':
            self.current_interaction.append(p.match.query)
            self.current_interaction.append(data.matches['response'])
            self.end_interaction()
            return p.add(action='thanks.for.teaching')
        else:
            return p.add(action='ignore.learn')
