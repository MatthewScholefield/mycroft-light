import urllib.request

import requests
from hashlib import md5
from requests import request, get as request_get
from urllib.parse import urlparse, quote
from urllib.request import urlopen

from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log


class RemoteKeyService(ServicePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        self.url_plugins = {}

        urllib.request.urlopen = self.urlopen
        requests.request = self.request
        requests.get = self.request_get

    def create_key(self, host: str, path: str) -> str:
        log.debug('Registered remote', path, 'key for', host)
        self.url_plugins[host] = path
        return md5(path.encode()).hexdigest()

    def modify_url(self, url: str) -> str:
        parts = list(urlparse(url))

        plugin_name = self.url_plugins.get(parts[1])
        if not plugin_name:
            if parts[1].startswith('www.'):
                plugin_name = self.url_plugins.get(parts[1].replace('www.', ''))
            if not plugin_name:
                return url
        server_root = '{}/{}/{}/plugin/{}'.format(
            self.rt.config['server']['url'],
            self.rt.identity.uuid,
            quote(self.rt.identity.access_token),
            plugin_name
        )
        log.debug('Injecting key for', plugin_name)
        return url.replace(parts[0] + '://' + parts[1], server_root)

    def urlopen(self, url, *args, **kwargs):
        log.debug('GET {}'.format(url))
        url = self.modify_url(url)
        return urlopen(url, *args, **kwargs)

    def request(self, url, *args, **kwargs):
        url = self.modify_url(url)
        return request(url, *args, **kwargs)

    def request_get(self, url, *args, **kwargs):
        url = self.modify_url(url)
        print('NeW:', url)
        return request_get(url, *args, **kwargs)
