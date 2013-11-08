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
        self.s_config = {}

        if s_config is not None:
            self.load_server_config(s_config)

        if c_config is not None:
            self.load_client_config(c_config)

    def load_server_config(self, s_config):
        """
        Server configuration is a json string.
        """

        c = json.loads(s_config)
        self.jid = c.pop('jid')
        self.password = c.pop('password')
        self.host = c.pop('host', self.host)
        self.port = int(c.pop('port', self.port))
        self.s_config = c

    @property
    def address(self):
        if self.host is None:
            return None
        return (self.host, self.port)

    def is_alive(self):
        return True

    def load_client_config(self, c_config):
        self.config.update(json.loads(c_config))

    def setup_client(self):
        """
        To be customized by client implementations.
        """

    def register_client(self, client):
        self.client = client
        self.setup_client()

    def make_client(self):
        client = self._client_cls(self.jid, self.password)
        return client

    def connect(self):
        if self.client is not None:
            logger.info('Bot appears to be connected.')
            return
        client = self.make_client()
        self.register_client(client)
        self.client.connect(address=self.address, **self.s_config)
        self.client.process(block=False)

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


class MucBotCore(BotCore):
    """
    The base jabber bot class.
    """

    def make_client(self):
        client = super(MucBotCore, self).make_client()

        self.setup_plugins(client, [
            'xep_0030',  # Service discovery
            'xep_0045',  # Multi-User Chat
            'xep_0199',  # XMPP Ping
        ])

        self.setup_events(client, [
            ('session_start', self.join_rooms),
        ])

        self.muc = client.plugin['xep_0045']
        return client

    def join_rooms(self, event):
        rooms = self.config.get('rooms', [])
        self.nickname = self.config.get('nickname', self.client.boundjid.user)

        for room in rooms:
            self.muc.joinMUC(room, self.nickname, wait=True)


class Command(object):
    """
    Core bot command class.
    """

    def __init__(self, *a, **kw):
        pass
