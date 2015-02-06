import logging
from collections import namedtuple

logger = logging.getLogger('mtj.jibber.testing')

_Jid = namedtuple('Jid', ['user', 'bare', 'resource'])

class Jid(_Jid):
    def __str__(self):
        return '%s/%s' % (self.bare, self.resource)


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
        self.full_sent = []
        self.scheduler = []
        self.schedules = {}

        self.boundjid = Jid('Testbot', 'Testbot@example.com', 'Tester')

        self.defaults.update(kw)

    def schedule(self, name, *a, **kw):
        if name in self.schedules:
            raise ValueError
        self.schedules[name] = (a, kw)
        self.scheduler.append((a, kw))

    def send_message(self, mto, mbody, *a, **kw):
        logger.debug('args = %s', a)
        logger.debug('kwargs = %s', kw)
        logger.info(mbody)
        self.sent.append(mbody)
        self.full_sent.append(dict(mto=mto, mbody=mbody, **kw))

    def register_plugin(self, plugin):
        self.plugins.append(plugin)

    def add_event_handler(self, *a):
        self.events.append(a)
        if a[0] == 'groupchat_message':
            self.groupchat_message_handlers.append(a[1])

    def disconnect(self):
        pass

    def _clear(self):
        self.sent = []

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


class TestMuc(object):

    def __init__(self, *a, **kw):
        self.joined_rooms = []

    def joinMUC(self, room, nickname, **kw):
        self.joined_rooms.append((nickname, room))
