from mtj.jibber.core import Command


class Greeter(object):

    def say_hi(self, msg, match, bot=None):
        """
        msg - the message stanza from the jabber client.
        match - the match regexp object.
        """

        return 'hi %(mucnick)s' % msg

    def say_legacy_hi(self, msg, match):
        return 'hi %(mucnick)s' % msg

    def say_hello_all(self, *a, **kw):
        return 'hello all'


class GreeterCommand(Command, Greeter):
    def __init__(self, *a, **kw):
        self.a = str(a)
        self.kw = str(kw)
        self.listened = []

    def say_a(self, msg, match, bot=None):
        return self.a

    def say_kw(self, msg, match, bot=None):
        return self.kw

    def listener(self, msg, match=None, bot=None):
        return self.listened.append(msg)

    def repeat_you(self, msg, match=None, bot=None):
        return msg['body']

    def to_one_target(self, msg, match=None, bot=None):
        return {
            'raw': 'hello target',
            'mto': msg.get('mucroom', 'devnull@example.com')
        }

    def to_multi_target(self, msg, match=None, bot=None):
        return [
            {
                'raw': 'test123',
                'mto': 'beacon@example.com',
            },
            {
                'raw': '42',
                'mto': 'answer@example.com',
            },
        ]

    def to_trap(self, msg, match=None, bot=None):
        return [
            {
                'raw': 'pretrap',
                'mto': 'trap@example.com',
            },
            None,  # the trap
            {
                'raw': 'posttrap',
                'mto': 'trap@example.com',
            },
        ]
