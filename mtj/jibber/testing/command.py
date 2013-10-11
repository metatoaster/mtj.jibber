from mtj.jibber.core import Command


class Greeter(object):

    def say_hi(self, msg, match):
        """
        msg - the message stanza from the jabber client.
        match - the match regexp object.
        """

        return 'hi %(mucnick)s' % msg

    def say_hello_all(self, *a, **kw):
        return 'hello all'


class GreeterCommand(Command, Greeter):
    def __init__(self, *a, **kw):
        self.a = str(a)
        self.kw = str(kw)
        self.listened = []

    def say_a(self, msg, match):
        return self.a

    def say_kw(self, msg, match):
        return self.kw

    def listener(self, msg, match=None):
        return self.listened.append(msg)
