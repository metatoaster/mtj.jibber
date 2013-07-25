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

    def setup_client(self, client):
        """
        Client is a SleekXMPP client.
        """

        super(MucChatBot, self).setup_client(client)

        self.setup_events(client, [
            ('groupchat_message', self.run_command),
        ])

        # nickname can be undefined, but we need this to check regex.
        self.nickname = self.config.get('nickname', 'bot')

        self.setup_commands()

    def setup_commands(self):
        """
        This is a fairly unsafe method.  Check your configs source.
        """

        self.objects = {}
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

    def setup_command_triggers(self, package, commands):
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

            f = getattr(self.objects[package], method)
            raw_reply = f(msg, match)
            if not raw_reply:
                continue

            # Okay we finally have a match.
            matched += 1
            self.send_message(mtype='groupchat', mto=msg['mucroom'],
                raw=raw_reply,)

    def send_message(self, mto, raw, **kwargs):
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
