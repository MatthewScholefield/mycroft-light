from copy import deepcopy
from mycroft_core import MycroftSkill, Package, intent_prehandler

from mycroft.util.text import compare


class IntrospectionSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.rt.query.on_response(self.on_response)
        self.last_packages = []

    def on_response(self, p: Package):
        self.last_packages = self.last_packages[-5:] + [deepcopy(p)]

    @intent_prehandler('what.skill.was.that')
    def handle_what_skill(self, p: Package):
        if not self.last_packages:
            return p.add(confidence=0.1)
        if 'phrase' not in p.match:
            last_package = self.last_packages[-1]
        else:
            phrase = p.match['phrase']
            best_match = max(self.last_packages, key=lambda x: compare(phrase, x.match.query))
            best_conf = compare(phrase, best_match.match.query)
            if best_conf < 0.5:
                return p.add(action='no.matching.query', data=dict(phrase=phrase))
            last_package = best_match
        return p.add(data=dict(
            skill=last_package.skill, intent=last_package.match.intent_id.split(':')[0]
        ))
