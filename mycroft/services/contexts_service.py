from typing import List, Any

from mycroft.intent_context import IntentContext
from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log


class ContextsService(ServicePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        self.contexts = {}
        self.context_providers = {}

    def get(self, name, intents: List[Any], intent_engine='file', skill_name=None) -> IntentContext:
        """Get a shared intent context or register one sourcing from the given skill"""
        if name not in self.contexts:
            skill_name = skill_name or 'shared_intent'
            context = IntentContext(self.rt, skill_name)
            for intent in intents:
                context.register(intent, intent_engine)
            self.context_providers[name] = skill_name
            self.contexts[name] = context
        elif skill_name:
            log.debug('{} context provided by {}. Ignoring data from {}.'.format(
                name, self.context_providers[name], skill_name
            ))
        return self.contexts[name]
