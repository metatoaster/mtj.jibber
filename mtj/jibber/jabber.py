import importlib
import logging
import re
import json
from collections import deque

from sleekxmpp import ClientXMPP

from mtj.jibber.core import BotCore
from mtj.jibber.core import MucBotCore
from mtj.jibber.core import Command

from mtj.jibber.utils import strip_tags

logger = logging.getLogger('mtj.jibber.jabber')


class MucChatBot(MucBotCore):
    """
    Bot that will parse the same config for a list of regex commands and
    the appropriate responses.
    """

    def setup_client(self):
        """
        Client is a SleekXMPP client.
        """

        client = self.client

        self.setup_events(client, [
            # bot might make fun of commands independently before doing
            # them...  actually, might depend on how the xmpp library
            # order this internally.
            ('groupchat_message', self.run_commentator),
            ('groupchat_message', self.run_command),
            ('groupchat_message', self.run_listener),
        ])

        # nickname can be undefined, but we need this to check regex.
        self.nickname = self.config.get('nickname', 'bot')

        self.setup_packages()

    def setup_packages(self):
        """
        This is a fairly unsafe method.  Check your configs source.

        Should really be a setup_packages thing.
        """

        self.objects = {}
        self.timers = {}
        self.commands = []
        self.commands_max_match = self.config.get('commands_max_match', 1)
        self.commentary_qsize = self.config.get('commentary_qsize', 2)

        # can't have zero-sized queue for this, see setup using this
        assert self.commentary_qsize > 0

        packages = self.config.get('packages')
        commands_packages = self.config.get('commands_packages')

        # verify sanity of this
        if not packages:
            if not commands_packages:
                logger.warning('`packages` are not defined, aborting.')
                return
            packages = commands_packages
            logger.warning('`commands_packages` is deprecated.  '
                  'It is now renamed to `packages`.')

        for package in packages:
            self.setup_package(**package)

    def setup_package(self, package, kwargs, **configs):
        ns, clsname = package.rsplit('.', 1)
        cls = getattr(importlib.import_module(ns), clsname)

        if not issubclass(cls, Command):
            logger.warning(
                'module `%s` is not a subclass of mtj.jibber.core.Command',
                package)
            return

        obj = cls(**kwargs)
        obj.bot = self
        self.objects[package] = obj
        self.setup_triggers(package, **configs)
        self.setup_listeners(package, **configs)
        self.setup_commentators(package, **configs)
        self.setup_timers(package, **configs)

    def setup_triggers(self, package, commands=None, **configs):
        if not commands:
            return

        for command in commands:
            try:
                trigger, method = command

                # this is to validate that this is a regex.
                rawregex = trigger % {
                    'nickname': self.nickname,
                }
                regex = re.compile(rawregex, re.IGNORECASE)

                self.commands.append((trigger, package, method))
            except:
                logger.exception('%s is an invalid command', command)

    def setup_listeners(self, package, listeners=None, **configs):
        self.listeners = []

        if not listeners:
            return

        for listener in listeners:
            # this is to validate that this is a regex.
            self.listeners.append((package, listener))

    def setup_commentators(self, package, commentators=None, **configs):
        """
        Commentators are things that observe the channel and may speak
        the results into the channel.  Use with care

        Generally it will avoid doing metacommentary, because that can
        lead to hilarious never ending loop.  So to avoid that a queue
        is used, controlled by `commentary_qsize`, so that the handler
        will be able to avoid doing this.
        """

        self.commentators = []
        # XXX assuming CPython implementation where this is thread-safe.
        # As sleekxmpp is multithreaded, this may be a problem in other
        # implementations of Python.
        self.commentary = deque([], self.commentary_qsize)

        if not commentators:
            return

        for commentator in commentators:
            trigger, method = commentator
            self.commentators.append((trigger, package, method))

    def setup_timers(self, package, timers=None, **configs):
        """
        Timers are in this format:

            "timers": [
                {
                    "mtype": "groupchat",
                    "mto": "testing@chat.example.com",
                    "schedule": [
                        {"seconds": 7200, "method": "say_hello"},
                        {"seconds": 1800, "method": "report_time"}
                    ]
                }
            ]

        """

        if not timers:
            return

        for timer in timers:
            self.setup_schedule(package, **timer)

    def setup_schedule(self, package, schedule, **msg_kwargs):
        for schedule in schedule:
            seconds = schedule['seconds']
            method = schedule['method']
            if not isinstance(seconds, int):
                logger.error('the value `%s` is not an int',
                    seconds.__repr__())
                continue
            self.timers[(package, method)] = (seconds, msg_kwargs)

        for timer in self.timers.keys():
            self.register_timer(timer)

    def register_timer(self, args):
        try:
            self.client.scheduler.remove(str(args))
        except ValueError:
            pass
        seconds, kwargs = self.timers[args]

        # If the sleekxmpp _event_runner method actually can cope with
        # the extra kwargs argument supported by the schedule method...
        # Oh well, workaround works like this.  It's wrappers all the
        # way down.
        self.client.schedule(str(args), seconds, self.run_timer,
            (self.send_package_method, args, kwargs), repeat=True)

    def run_command(self, msg):
        if msg['mucnick'] == self.nickname:
            return

        matched = 0
        for command, package, method in self.commands:
            if matched >= self.commands_max_match:
                break

            # nickname may have changed?
            rawregex = command % {
                'nickname': self.nickname,
            }
            regex = re.compile(rawregex, re.IGNORECASE)

            match = regex.search(msg['body'])
            if not match:
                continue

            if self.send_package_method(package, method, msg=msg, match=match,
                    mto=msg['mucroom'], mtype='groupchat'):
                # Okay we have a match.
                matched += 1

    def run_listener(self, msg):
        if msg['mucnick'] == self.nickname:
            # never listen to self.
            return

        for package, method in self.listeners:
            f = getattr(self.objects[package], method)
            try:
                f(msg=msg)
            except:
                logger.exception('Error calling listener')

    def run_commentator(self, msg):
        # verify that this message is not generated by recent commentary
        # made by this bot, even though (meta)*commentator may be a
        # hilarious concept to some.

        # Only comment once, so do so carefully.

        if msg['mucnick'] == self.nickname and msg['body'] in self.commentary:
            return

        for command, package, method in self.commentators:
            # nickname may have changed?
            rawregex = command % {
                'nickname': self.nickname,
            }
            regex = re.compile(rawregex, re.IGNORECASE)

            match = regex.search(msg['body'])
            if not match:
                continue

            sent_msg = self.send_package_method(
                package, method, msg=msg, match=match,
                mto=msg['mucroom'], mtype='groupchat')

            if sent_msg:
                # remember what we said
                self.commentary.append(sent_msg)
                # and we are done; maximum one commentary for now.
                break


    def run_timer(self, method, args, kwargs):
        return method(*args, **kwargs)

    def send_package_method(self, package, method, **kwargs):
        f = getattr(self.objects[package], method)
        try:
            msg = kwargs.pop('msg', {})
            match = kwargs.pop('match', None)
            raw_reply = f(msg=msg, match=match)
        except:
            logger.exception('Failed to send_package_method')
            return

        if isinstance(raw_reply, basestring):
            self.send_message(raw=raw_reply, **kwargs)

        # reset the timer if it's in timer
        # XXX some other method should do this check?
        if self.timers.get((package, method)):
            self.register_timer((package, method))

        return raw_reply

    def send_message(self, raw, mto, **kwargs):
        # TODO make a better way to determine if HTML.
        if (raw.startswith('<p>') or raw.startswith('<html>') or
                raw.startswith('<!')):
            reply_html = str(raw)
            reply_txt = strip_tags(raw)
        else:
            reply_html = None
            reply_txt = raw

        self.client.send_message(mto, mbody=reply_txt, mhtml=reply_html,
            **kwargs)
