import importlib
from imp import reload
import logging
import re
import json
import random
import sys
from collections import deque
from functools import partial

from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream import ET

from mtj.jibber.core import BotCore
from mtj.jibber.core import MucBotCore
from mtj.jibber.core import Handler

from mtj.jibber.utils import strip_tags

logger = logging.getLogger('mtj.jibber.jabber')

if sys.version_info > (3, 0):  # pragma: no cover
    unicode = str


class MucChatBot(MucBotCore):
    """
    Bot that will parse the same config for a list of regex commands and
    the appropriate responses.
    """

    _muc_setup = False

    def setup_client(self):
        """
        Client is a SleekXMPP client.
        """

        if self._muc_setup:
            logger.warning('Client already setup.')
            return

        client = self.client

        self.groupchat_message_handlers = [
            # bot might make fun of commands independently before doing
            # them...  actually, might depend on how the xmpp library
            # order this internally.
            self.run_commentator,
            self.run_command,
            self.run_listener,
        ]

        self.message_handlers = [
            self.run_private_command,
        ]

        self.setup_events(client, [('groupchat_message', f) for f in
            self.groupchat_message_handlers])

        self.setup_events(client, [('message', f) for f in
            self.message_handlers])

        if not self.nickname:
            # nickname can be undefined if normal client init workflow
            # is avoided, but we still need this available as a string.
            self.nickname = self.config.get('nickname') or 'bot'

        self._muc_setup = True

        self.setup_packages()

    @property
    def raw_handlers(self):
        # XXX this actually should NEVER be cleared since we only want
        # to keep one instance of the partial that will do the resolving
        # to the local instance methods.  Moved from setup_packages as
        # the bot_reinit will call that.
        result = getattr(self, '_raw_handlers', None)
        if result is None:
            result = self._raw_handlers = {}
        return result

    def clear_timers(self):
        """
        Removes _all_ timers from the scheduler.
        """

        timers = getattr(self, 'timers', {})

        for args, v in timers.items():
            try:
                self.client.scheduler.remove(str(args))
            except ValueError:
                pass

        self.timers = {}

    def setup_packages(self):
        """
        This is a fairly unsafe method.  Check your configs source.

        Should really be a setup_packages thing.
        """

        self.commands_max_match = self.config.get('commands_max_match', 1)
        self.commentary_qsize = self.config.get('commentary_qsize', 2)

        self.objects = {}
        self.clear_timers()
        self.private_commands = []
        self.commands = []
        self.listeners = []
        self.commentators = []

        for k in self.raw_handlers.keys():
            # have to clear the lists, too.
            self.raw_handlers[k] = []

        # can't have zero-sized queue for this, see setup using this
        if not self.commentary_qsize > 0:
            raise ValueError('commentary_qsize must be greater than 0')

        # XXX assuming CPython implementation where this is thread-safe.
        # As sleekxmpp is multithreaded, this may be a problem in other
        # implementations of Python.
        self.commentary = deque([], self.commentary_qsize)

        packages = self.config.get('packages')

        for package in packages:
            self.setup_package(**package)

        for timer in self.timers.keys():
            self.register_timer(timer)

    def setup_package(self, package, kwargs=None, alias=None, **configs):
        if kwargs is None:
            kwargs = {}

        ns, clsname = package.rsplit('.', 1)
        mod = importlib.import_module(ns)
        # force module reloading.
        mod = reload(mod)
        cls = getattr(mod, clsname)

        if not issubclass(cls, Handler):
            logger.warning(
                'module `%s` is not a subclass of mtj.jibber.core.Handler',
                package)
            return

        obj = cls(**kwargs)
        if alias is None:
            alias = package
        self.objects[alias] = obj

        self.setup_package_instance(alias, **configs)

    def setup_package_instance(self, package, **configs):
        # XXX the parameter `package` was really mapped to a package, but
        # is now a name.
        self.setup_private_commands(package, **configs)
        self.setup_commands(package, **configs)
        self.setup_listeners(package, **configs)
        self.setup_commentators(package, **configs)
        self.setup_timers(package, **configs)
        self.setup_raw_handlers(package, **configs)

    def setup_private_commands(self, package, private_commands=None,
            **configs):
        if not private_commands:
            return

        for command in private_commands:
            try:
                trigger, method = command
                # this is to validate that this is a regex.
                regex = re.compile(trigger, re.IGNORECASE)
                self.private_commands.append((trigger, package, method))
            except:
                logger.exception('%s maps to an invalid private command',
                    command)

    def setup_commands(self, package, commands=None, **configs):
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

        Maybe we might want a way to allow for variance?

        """

        if not timers:
            return

        for timer in timers:
            self.setup_schedule(package, **timer)

    def setup_schedule(self, package, schedule, **msg_kwargs):
        for schedule in schedule:
            seconds = schedule['seconds']
            method = schedule['method']
            if isinstance(seconds, int):
                self.timers[(package, method)] = (seconds, msg_kwargs)
                continue

            try:
                x, y = seconds
                if isinstance(x, int) and isinstance(y, int):
                    self.timers[(package, method)] = ((x, y), msg_kwargs)
                    continue
            except (ValueError, TypeError):
                pass

            logger.error(
                'the value `%s` is invalid for timer `%s` in package `%s`; '
                'valid value is either an int or a tuple of two integers '
                'specifying the range of possible delays.  Ignored.',
                seconds.__repr__(), method, package)

    def setup_raw_handlers(self, package, raw_handlers=None, **configs):
        if not raw_handlers:
            return

        for event, method_name in raw_handlers.items():
            if not event in self.raw_handlers:
                self.raw_handlers[event] = []
                self.client.add_event_handler(event,
                    partial(self.run_raw_handler, event))
            self.raw_handlers[event].append((package, method_name))

    def register_timer(self, args):
        try:
            self.client.scheduler.remove(str(args))
        except ValueError:
            logger.warning('%s not in schedule?', args)
            pass
        seconds, kwargs = self.timers[args]

        if isinstance(seconds, tuple):
            seconds = random.randint(*seconds)
            logger.debug('%s will happen in %d', args, seconds)

        self.client.schedule(str(args), seconds, self.run_timer,
            (self.send_package_method, args, kwargs), repeat=False)

    def run_private_command(self, msg):
        if msg.get('type') != 'chat':
            return
        for rawregex, package, method in self.private_commands:
            logger.debug('received:%s', msg)
            regex = re.compile(rawregex, re.IGNORECASE)
            match = regex.search(msg['body'])
            if not match:
                continue
            self.send_package_method(package, method, msg=msg, match=match,
                mto=msg.get('from'))

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
                f(msg=msg, bot=self)
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
        result = method(*args, **kwargs)
        return result

    def run_raw_handler(self, event, msg):
        # XXX log multiple calls with same msg?
        # XXX warn for missing event key in raw_handlers?
        for package, method_names in self.raw_handlers.get(event, {}):
            for method_name in method_names:
                f = getattr(self.objects[package], method_name, None)
                if not f:
                    logger.error('%s.%s does not exist.',
                        self.objects[package], method_name)
                    continue
                try:
                    f(msg=msg, bot=self)
                except:
                    logger.exception('Error running raw_handler for event %s, '
                        'in method %s.%s', event, package, method_name)

    def send_package_method(self, package, method, **kwargs):

        try:
            f = getattr(self.objects[package], method)
            msg = kwargs.pop('msg', {})
            match = kwargs.pop('match', None)
            raw_reply = f(msg=msg, match=match, bot=self)
        except:
            logger.exception('Failed to send_package_method')
            return

        self.process_send_requests(raw_reply, **kwargs)

        # reset the timer if it's in timer; this is useful if there
        # exist a command (or other triggers such as timer) triggered
        # this, so that things can be rescheduled.
        if self.timers.get((package, method)):
            self.register_timer((package, method))

        return raw_reply

    def process_send_requests(self, raw_reply, **kwargs):
        """
        Process the result returned by the package methods.  This will
        in turn call send_message as appropriate for replies.
        """

        def send_raw(raw_reply):
            response = {}
            response.update(kwargs)
            response.update(raw_reply)
            self.send_message(**response)

        def send_check(raw_reply):
            if type(raw_reply) in (str, unicode):
                self.send_message(raw=raw_reply, **kwargs)
            elif isinstance(raw_reply, dict):
                send_raw(raw_reply)

        if isinstance(raw_reply, list):
            for r in raw_reply:
                send_check(r)
        else:
            send_check(raw_reply)

    def send_message(self, mto, raw=None, **kwargs):
        """
        Shorthanded send_message method that will auto-detect input and
        process them into the correct mbody and mhtml arguments before
        passing that to the underlying client's send_message method if
        and only if the relevant kwargs are not also provided, as it
        will also pass along all the kwargs.

        Rules of argument handling:

        - `raw` argument takes the lowest priority.  Do not pass along
          `mbody` or `mhtml` arguments if this default shortcut to
          generate both HTML and plain text is desired.  Conversion to
          html will be triggered `mhtml` is not already specified, and
          if an expected start-tag is detected (which is any strings that
          starts with `<p>`, `<html>` or `<body>` (case-insensitive), and
          then leaving the `mbody` with the same value but with all html
          tags stripped.

        - `mbody` will never be converted to html or have tags stripped,
          however if a `raw` value is provided, any html derived as per
          above will be passed as `mhtml`.

        - `mhtml` will be converted using `sleekxmpp.xmlstream.ET.XML`
          into html.  On success, HTML will be sent along with the
          plain text as derived using the above rules.  Failure will
          mean that no HTML will be sent, instead the `raw` or `mbody`
          will be sent as plain text.
        """

        # see if we can skip dealing with html
        _mbody = kwargs.pop('mbody', None)
        mhtml = kwargs.pop('mhtml', None)
        mbody = _mbody or raw

        if not type(mbody) in (str, unicode):
            if mhtml:
                # TODO add info on what package caused this and elevate to
                # warning
                logger.info('raw or detected body is not a string but html '
                    'was specified, however this is ignored.')
            # just simply fail this, until we have a better way to track
            # this.
            return

        if mhtml is None and type(raw) in (str, unicode):
            # figure out if we can coerce the raw string into html
            # just check first-n characters.
            ss = raw[:10].lower()
            checks = ('<p>', '<html>', '<body>',)

            if any((ss.startswith(check) for check in checks)):
                # raw is an html candidate.
                mhtml = raw

        # now attempt html conversion.
        if not mhtml is None:
            try:
                mhtml = ET.XML(mhtml)
                if _mbody is None:
                    # mbody not explicitly defined
                    mbody = strip_tags(raw)
            except ET.ParseError:
                logger.warning(
                    'An attempt to send the following as html has failed.'
                    '----------\n%s'
                    '\n----------\n'
                    'retrying with just plain text', mhtml
                )
                # no more html
                mhtml = None

        try:
            # TODO verify that values to be sent doesn't have control
            # characters which cause disconnection?  At least no more
            # crashes.
            self.client.send_message(mto=mto, mbody=mbody, mhtml=mhtml,
                **kwargs)
        except Exception:
            logger.exception('send_message somehow failed! message: %s', {
                'mto': mto,
                'mbody': mbody,
                'mhtml': mhtml,
                'kwargs': kwargs,
            })
