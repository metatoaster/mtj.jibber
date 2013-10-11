import logging
from collections import namedtuple

logger = logging.getLogger('mtj.jibber.testing')

Jid = namedtuple('Jid', 'user')


class TestClient(object):
    """
    Provide an emulation of client msg communication.
    """

    def __init__(self, **kw):
        self.plugins = []
        self.events = []
        self.defaults = {
            'mucnick': "Tester",
        }

        self.sent = []

        self.boundjid = Jid('Testbot',)

        self.defaults.update(kw)

    def send_message(self, mbody, *a, **kw):
        logger.debug('args = %s', a)
        logger.debug('kwargs = %s', kw)
        sent = '%s: %s' % (self.bot.nickname, mbody)
        logger.info(sent)
        self.sent.append(sent)

    def register_plugin(self, plugin):
        self.plugins.append(plugin)

    def add_event_handler(self, *a):
        self.events.append(a)

    def _clear(self):
        self.sent.clear()
