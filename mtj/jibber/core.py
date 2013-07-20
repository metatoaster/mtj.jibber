import logging
import re
import json

from sleekxmpp import ClientXMPP

logger = logging.getLogger('mtj.jibber.core')


class BotCore(object):
    """
    The base jabber bot class.
    """

    _client_cls = ClientXMPP

    def __init__(self, s_config=None):
        self.jid = None
        self.password = None
        self.host = None
        self.port = 5222

        self.client = None

        if s_config is not None:
            self.load_server_config(s_config)

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

    def connect(self):
        if self.client is not None:
            logger.info('Bot appears to be connected.')
            return
        client = self._client_cls(self.jid, self.password)
        client.connect(address=self.address)
        client.process(block=False)
        self.client = client

    def disconnect(self):
        self.client.disconnect()
        self.client = None
