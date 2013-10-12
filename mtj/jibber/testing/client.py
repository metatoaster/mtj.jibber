import logging
from collections import namedtuple

logger = logging.getLogger('mtj.jibber.testing')

Jid = namedtuple('Jid', 'user')


class TestClient(object):
    """
    Provide an emulation of client msg communication.
    """

    def __init__(self, *a, **kw):
        self.plugins = []
        self.events = []
        self.defaults = {
            'mucnick': "Tester",
            'mucroom': "testroom@chat.example.com",
        }

        self.groupchat_message_handlers = []
        self.sent = []
        self.scheduler = []

        self.boundjid = Jid('Testbot',)

        self.defaults.update(kw)

    def schedule(self, *a, **kw):
        pass

    def send_message(self, mto, mbody, *a, **kw):
        logger.debug('args = %s', a)
        logger.debug('kwargs = %s', kw)
        logger.info(mbody)
        self.sent.append(mbody)

    def register_plugin(self, plugin):
        self.plugins.append(plugin)

    def add_event_handler(self, *a):
        self.events.append(a)
        if a[0] == 'groupchat_message':
            self.groupchat_message_handlers.append(a[1])

    def disconnect(self):
        pass

    def _clear(self):
        self.sent.clear()

    def __call__(self, body, **kw):
        msg = {}
        msg['body'] = body
        msg.update(self.defaults)
        msg.update(kw)
        for h in self.groupchat_message_handlers:
            # XXX at some point once I figure out how to get handlers
            # to also receive the client, output redirection back to
            # here to allow both live and local tests at the same time.
            h(msg)
