from __future__ import unicode_literals  # we are using json anyway.

import argparse
import cmd
import code
import errno
import json
import logging
import os
import signal
import sys
import tempfile
import time

from mtj.jibber.jabber import MucChatBot


class JibberCmd(cmd.Cmd):

    def __init__(self, bot):
        self.prompt = 'jibber> '
        self.pidfile = 'jibber.pid'
        cmd.Cmd.__init__(self)
        self.bot = bot
        self.loop = True
        self.timeout = 1

    def do_fg(self, arg):
        """
        run this in the foreground.
        """

        self.bot.connect()
        while self.loop:
            try:
                time.sleep(self.timeout)
                self.loop = self.bot.is_alive()
            except KeyboardInterrupt:
                self.loop = False
            except:
                print('bot is dying in a fire, attempting to abort...')
                self.loop = False
        self.bot.disconnect()

    def do_debug(self, arg):
        """
        start the python debugger with the environment instantiated.
        """

        def bot_test():
            if self.bot.client is not None:
                print("Error: Bot already has an active client.")
                return

            from mtj.jibber.testing.client import TestClient
            self.bot.client = TestClient()
            self.bot.setup_client()
            console.locals[b'client'] = self.bot.client
            print("Test client ready; call client('Hello bot') to interact.")

        console = code.InteractiveConsole(locals={
            'bot': self.bot,
            'bot_test': bot_test,
        })

        result = console.interact(
            'Starting interactive shell. '
            '`bot` is bound to the MucBot object.\n'
            'Try calling bot.connect() to connect to the server specified.\n'
            'Note: process will NOT terminate if bot.is_alive() is False!\n'
            'Alternatively call bot_test() to test here locally.')
        self.bot.disconnect()

    def do_EOF(self, arg):
        print('')
        return 1


class GenerateConfig(argparse.Action):
    targets = {
        'server': 'server.config.json.example',
        'client': 'muc_bot.client.config.json.example',
        'client_example': 'muc_bot_extended.client.config.json.example',
    }

    def __call__(self, parser, namespace, values, option_string=None):
        target = self.targets.get(values)
        if target:
            print(read_config(os.path.join(os.path.dirname(__file__),
                'configs', target)).strip())
            sys.exit(0)
        print('Valid template ids are: %s' % ', '.join(self.targets.keys()))
        sys.exit(2)


def get_argparsers():
    parser = argparse.ArgumentParser(description='Controller for mtj.jibber.')

    sp = parser.add_argument('server_config', metavar='<server_config>',
        help='Server configuration file, only includes credentials for server')
    sp = parser.add_argument('client_config', metavar='<client_config>',
        help='Client configuration file, defines what packages are used where')

    sp = parser.add_subparsers(dest='command')
    sp_fg = sp.add_parser(r'fg', help='Run %(prog)s in foreground')
    sp_debug = sp.add_parser(r'debug', help='Open a debug python shell')
    sp_console = sp.add_parser(r'console', help='Console mode (default)')

    parser.add_argument('--gen-config', action=GenerateConfig,
        help='Generate a skeleton configuration file from this set of '
            'template ids: server, client, client_example.')

    parser.set_defaults(command='console')

    return parser, sp

def read_config(config):
    try:
        with open(config) as fd:
            return fd.read()
    except IOError:
        print('cannot load config file `%s`' % config)

def main(args=None, _bot_cls=MucChatBot, _cmd_cls=JibberCmd):
    if args is None:
        args = sys.argv[1:]

    _default = 'console'
    parser, sp = get_argparsers()

    # workaround for python2.7's incorrect(?) default usage.
    # won't be needed in python3.3.
    if not set.intersection(set(args), set(sp.choices.keys())):
        args.append(_default)

    parsed_args = parser.parse_args(args)

    s_config = read_config(parsed_args.server_config)
    c_config = read_config(parsed_args.client_config)

    if not s_config or not c_config:
        return

    # Python versions before 3.0 do not use UTF-8 encoding
    # by default. To ensure that Unicode is handled properly
    # throughout SleekXMPP, we will set the default encoding
    # ourselves to UTF-8.

    if sys.version_info < (3, 0): # pragma: no cover
        from sleekxmpp.util.misc_ops import setdefaultencoding
        setdefaultencoding('utf8')

    bot = _bot_cls()
    bot.load_server_config(s_config)
    bot.load_client_config(c_config)

    c = _cmd_cls(bot)

    # TODO make these logging configurable from the client_config
    logging.basicConfig(
        level='INFO',
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )

    try:
        import readline
    except ImportError:  # pragma: no cover
        pass

    if parsed_args.command and parsed_args.command != _default:
        cmdarg = getattr(parsed_args, 'cmdarg', '')
        return c.onecmd(parsed_args.command + ' ' + cmdarg)
    else:  # interactive mode
        c.cmdloop()
