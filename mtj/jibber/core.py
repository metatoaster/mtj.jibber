import logging
import re
import json

from sleekxmpp import ClientXMPP

from mtj.jibber.utils import ConfigFile

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
        self.s_config = {}  # server config is distinct.

        self._raw_config = None
        self._raw_s_config = {}  # server config helper is distinct.

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

    def load_client_config(self, c_config):
        return self.config.update(json.loads(c_config))

    def load_server_config_from_path(self, s_config_path):
        self._raw_s_config = ConfigFile(s_config_path, self.load_server_config)
        return self._raw_s_config.load()

    def load_client_config_from_path(self, c_config_path):
        self._raw_config = ConfigFile(c_config_path, self.load_client_config)
        return self._raw_config.load()

    def reload_client_config(self):
        self.config.clear()
        if self._raw_config:
            return self._raw_config.load()

    @property
    def address(self):
        if self.host is None:
            return None
        return (self.host, self.port)

    def is_alive(self):
        return True

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


class Handler(object):
    """
    Base handler type.
    """

    def __init__(self, *a, **kw):
        pass


class Command(Handler):
    """
    Core bot command class.  Methods defined here that are to be added
    as package methods for the bot core should take these arguments:

    msg
        the message stanza
    match
        the matched regex groups
    bot
        the bot instance that raised this match.
    """


class Presence(Handler):
    """
    The presence type.  Should be used for all presence handlers.
    Arguments for valid methods should follow this:

    msg
        the presence stanza
    bot
        the bot instance that raised this.
    """
