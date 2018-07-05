import urllib.request
from functools import wraps

import requests
from hashlib import md5
from urllib.parse import urlparse, quote

from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log


class RemoteKeyService(ServicePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        self.url_plugins = {}
        self.custom_urls = {}

        urllib.request.urlopen = self.wrap_function(urllib.request.urlopen)
        requests.request = self.wrap_function(requests.request, arg_index=1)
        requests.get = self.wrap_function(requests.get)

    def create_key(self, host: str, path: str, custom_url=None, use_auth=False) -> str:
        log.debug('Registered remote', path, 'key for', host)
        self.url_plugins[host] = path
        if custom_url or use_auth:
            self.custom_urls[path] = (custom_url, use_auth)
        return md5(path.encode()).hexdigest()

    def modify_url(self, url: str) -> str:
        parts = list(urlparse(url))

        plugin_name = self.url_plugins.get(parts[1])
        if not plugin_name:
            if parts[1].startswith('www.'):
                plugin_name = self.url_plugins.get(parts[1].replace('www.', ''))
            if not plugin_name:
                return url
        custom_url, use_auth = self.custom_urls.get(plugin_name, (None, False))
        server_root_format = custom_url or '{server_url}/{uuid}/{token}/plugin/{plugin}'
        server_root = server_root_format.format(
            server_url=self.rt.config['server_url'],
            uuid=self.rt.identity.uuid,
            token=quote(self.rt.identity.access_token),
            plugin=plugin_name
        )
        log.debug('Injecting key for', plugin_name)
        return url.replace(parts[0] + '://' + parts[1], server_root)

    def wrap_function(self, func, arg_index=0, arg_name='url'):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > arg_index:
                args = list(args)
                url = args[arg_index]
                args[arg_index] = self.modify_url(url)
            else:
                url = kwargs[arg_name]
                kwargs[arg_name] = self.modify_url(url)
            log.debug('REQ {}...'.format(url))
            return func(*args, **kwargs)
        return wrapper
