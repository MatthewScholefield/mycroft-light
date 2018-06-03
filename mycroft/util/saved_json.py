from fitipy import Fitipy


class SavedJson:
    """Dict that saves to disk on modifications"""

    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.fiti = Fitipy(self.filename)
        self.data = self.fiti.read().dict()

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        changed = self.data.get(key, ...) != value
        self.data[key] = value
        if changed:
            self.fiti.write().dict(self.data)

    def __delitem__(self, key):
        del self.data[key]
        self.fiti.write().dict(self.data)

    def get(self, k):
        return self.data.get(k)

    def update(self, data=None, **kwargs):
        self.data.update(data, **kwargs)
        self.fiti.write().dict(self.data)
