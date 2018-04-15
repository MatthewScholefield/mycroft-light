from abc import abstractmethod

from mycroft.base_plugin import BasePlugin
from mycroft.package_cls import Package


class TransformerPlugin(BasePlugin):
    """
    Class used to modify package states.
    For example, to replace a .dialog file with actual translated lines
    Add new attributes in the *constructor* with: self.rt.package.add_struct({'myattr': int})
    """
    @abstractmethod
    def process(self, p: Package):
        """Modify attributes in package"""
        pass
