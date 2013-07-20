import logging
import re
import json

from sleekxmpp import ClientXMPP

logger = logging.getLogger('mtj.jibber.core')


class BotCore(object):
    """
    The base jabber bot class.

    General use case might go something like this::

        client.load_server_config(server_configs)
        client.load_client_config(client_configs)
        client.connect()

    """

    _client_cls = ClientXMPP

    def __init__(self, s_config=None, c_config=None):
        self.jid = None
        self.password = None
        self.host = None
        self.port = 5222

        self.client = None
        self.config = {}

        if s_config is not None:
            self.load_server_config(s_config)

        if c_config is not None:
            self.load_client_config(c_config)

    def load_server_config(self, s_config):
        """
        Server configuration is a json string.
        """

        c = json.loads(s_config)
        self.jid = c.get('jid')
        self.password = c.get('password')
        self.host = c.get('host', self.host)
        self.port = int(c.get('port', self.port))

    @property
    def address(self):
        if self.host is None:
            return None
        return (self.host, self.port)

    def load_client_config(self, c_config):
        self.config.update(json.loads(c_config))

    def setup_client(self, client):
        """
        To be customized by client implementations.
        """

    def make_client(self):
        client = self._client_cls(self.jid, self.password)
        self.setup_client(client)
        return client

    def connect(self):
        if self.client is not None:
            logger.info('Bot appears to be connected.')
            return
        client = self.make_client()
        client.connect(address=self.address)
        client.process(block=False)
        self.client = client

    def disconnect(self):
        if self.client is None:
            return

        self.client.disconnect()
        self.client = None

    # shared setup methods

    def setup_plugins(self, client, plugins):
        for plugin in plugins:
            client.register_plugin(plugin)

    def setup_events(self, client, events):
        for event, handler in events:
            client.add_event_handler(event, handler)
