import importlib
import logging
import re
import json

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
            ('groupchat_message', self.run_command),
            ('groupchat_message', self.run_listener),
        ])

        # nickname can be undefined, but we need this to check regex.
        self.nickname = self.config.get('nickname', 'bot')

        self.setup_commands()

    def setup_commands(self):
        """
        This is a fairly unsafe method.  Check your configs source.
        """

        self.objects = {}
        self.timers = {}
        self.commands = []
        self.commands_max_match = self.config.get('commands_max_match', 1)

        commands_packages = self.config.get('commands_packages')

        # verify sanity of this
        if not commands_packages:
            logger.warning('`commands_package` is not defined, aborting.')
            return

        for package in commands_packages:
            self.setup_command_package(**package)

    def setup_command_package(self, package, kwargs, **configs):
        ns, clsname = package.rsplit('.', 1)
        cls = getattr(importlib.import_module(ns), clsname)

        if not issubclass(cls, Command):
            logger.warning(
                'module `%s` is not a subclass of mtj.jibber.core.Command',
                package)
            return

        self.objects[package] = cls(**kwargs)
        self.setup_command_triggers(package, **configs)
        self.setup_command_listeners(package, **configs)
        self.setup_command_timers(package, **configs)

    def setup_command_triggers(self, package, commands=None, **configs):
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

    def setup_command_listeners(self, package, listeners=None, **configs):
        self.listeners = []

        if not listeners:
            return

        for listener in listeners:
            # this is to validate that this is a regex.
            self.listeners.append((package, listener))

    def setup_command_timers(self, package, timers=None, **configs):
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
