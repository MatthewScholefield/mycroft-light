import json
from itertools import chain
from random import randint
from time import monotonic

from mycroft_core import MycroftSkill, Package, intent_prehandler, intent_handler
from mycroft.util import log


class DialogSkill(MycroftSkill):
    interaction_threshold = 100

    def __init__(self):
        super().__init__()
        self.just_responded = False
        self.last_interaction_time = monotonic()
        self.current_interaction = []
        self.all_interactions = self.load_interactions()
        self.responses = self.generate_responses()
        self.rt.query.on_query(self.on_query)

        self.learn_intents = self.intent_context(['unsure', 'learn.response'])

    @staticmethod
    def normalize(sentence):
        return sentence.lower().strip()

    def generate_responses(self):
        return dict(chain(*[
            chain(zip(map(self.normalize, i[::2]), i[1::2]),
                  zip(map(self.normalize, i[1::2]), i[2::2]))
            for i in self.all_interactions
        ]))

    def load_interactions(self):
        if self.filesystem.isfile('responses.json'):
            with self.filesystem.open('responses.json') as f:
                return json.load(f)
        return []

    def save_all_interactions(self):
        with self.filesystem.open('responses.json', 'w') as f:
            json.dump(self.all_interactions, f)

    def shutdown(self):
        log.info('Shutting down dialog...')
        self.interaction_threshold = 0
        self.update_interaction()
        self.save_all_interactions()
        self.rt.query.remove_on_query(self.on_query)

    def on_query(self, query):
        if not self.just_responded:
            self.last_interaction_time = 0
        self.just_responded = False

    def interaction_expired(self) -> bool:
        return monotonic() - self.last_interaction_time > self.interaction_threshold

    def end_interaction(self):
        for i, interaction in enumerate(self.all_interactions):
            if interaction[:len(self.current_interaction)] == self.current_interaction:
                self.all_interactions[i] = self.current_interaction
                break
        else:
            self.all_interactions.append(self.current_interaction)
        self.responses = self.generate_responses()
        self.current_interaction = []

    def update_interaction(self):
        if self.interaction_expired() and self.current_interaction:
            self.end_interaction()

    @intent_prehandler('fallback', '')
    def fallback(self, p: Package) -> Package:
        self.update_interaction()

        if p.match.query.lower() in self.responses:
            self.just_responded = True
            self.last_interaction_time = monotonic()
            data = self.responses[p.match.query]
            self.current_interaction.append(data)
            return p.add(confidence=0.8, speech=data)

        self.just_responded = False

        return p.add(confidence=0.0)

    @intent_handler('fallback', '')
    def fallback_handler(self, p: Package):
        if p.speech:
            return p

        self.just_responded = True
        data = self.get_response(self.package(action='learn'), self.learn_intents)
        if data.intent_id == 'learn.response':
            self.current_interaction.append(p.match.query)
            response = data.matches['response']
            self.current_interaction.append(response)
            self.end_interaction()
            return p.add(action='thanks.for.teaching')
        else:
            return p.add(action='ignore.learn')
