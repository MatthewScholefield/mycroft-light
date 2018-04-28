import urllib.request
from hashlib import md5
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen

from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log


class RemoteKeyService(ServicePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        self.url_plugins = {}

        urllib.request.urlopen = self.urlopen

    def create_key(self, host: str, path: str) -> str:
        log.debug('Registered remote', path, 'key for', host)
        self.url_plugins[host] = path
        return md5(path.encode()).hexdigest()

    def urlopen(self, url, *args, **kwargs):
        log.info('Intercepting url:', url)
        parts = list(urlparse(url))

        if parts[1] not in self.url_plugins:
            log.info(parts[1], 'NOT IN', self.url_plugins)
            return urlopen(url, *args, **kwargs)

        plugin_name = self.url_plugins[parts[1]]
        server_root = '{}/{}/{}/plugin/{}'.format(
            self.rt.config['server']['url'],
            self.rt.identity.uuid,
            urlencode(self.rt.identity.access_token),
            plugin_name
        )
        url = url.replace(parts[0] + '://' + parts[1], server_root)

        log.debug('GET {}'.format(url))
        return urlopen(url, *args, **kwargs)
