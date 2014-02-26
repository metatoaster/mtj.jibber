from unittest import TestCase
import json
import tempfile
import sys
from contextlib import contextmanager

from mtj.jibber import ctrl


# mixture of unicode and str in python2.7 version of argparse means that
# default IO classes would be painful to use; use my own thing here.
class Input(object):
    def __init__(self, inputs):
        self.inputs = inputs.splitlines()
    def readline(self):
        if self.inputs:
            return self.inputs.pop(0)
        else:
            raise EOFError

class Output(object):
    def __init__(self):
        self.items = []
    def write(self, s):
        self.items.append(s)


@contextmanager
def capture_stdio(inputs=''):
    dummy_in, dummy_out, dummy_err = Input(inputs), Output(), Output()
    curr_in, curr_out, curr_err = sys.stdin, sys.stdout, sys.stderr
    try:
        sys.stdin, sys.stdout, sys.stderr = dummy_in, dummy_out, dummy_err
        yield dummy_in, dummy_out, dummy_err
    finally:
        sys.stdin, sys.stdout, sys.stderr = curr_in, curr_out, curr_err


class FakeBot(object):
    connected = disconnected = 0
    alive = 1
    client = None
    def setup_client(self):
        pass
    def connect(self):
        self.connected += 1
    def disconnect(self):
        self.disconnected += 1
    def is_alive(self):
        self.alive -= 1
        return self.alive
    def load_server_config_from_path(self, cfg):
        return cfg[1:] or None
    def load_client_config_from_path(self, cfg):
        return cfg[1:] or None

class FakeCmd(object):
    def __init__(self, bot):
        self.bot = bot
    def onecmd(self, cmd):
        return cmd
    def cmdloop(self):
        pass

class NotBot(FakeBot):
    def is_alive(self):
        raise ValueError


class CtrlTestCase(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_main_empty_opts(self):
        with capture_stdio() as stdio:
            in_, out, err = stdio
            self.assertRaises(SystemExit, ctrl.main)
            self.assertTrue('usage:' in err.items[0])

    def test_main(self):
        args = ['server.json', 'client.json']
        ctrl.main(args, _bot_cls=FakeBot, _cmd_cls=FakeCmd)
        # workaround appended
        self.assertEqual(args[-1], 'console')

    def test_main_no_server_config(self):
        with capture_stdio() as stdio:
            in_, out, err = stdio
            args = ['s', ' ']
            ctrl.main(args, _bot_cls=FakeBot, _cmd_cls=FakeCmd)
            self.assertEqual(out.items[0], 'Server config file `s` not found.')

    def test_main_no_client_config(self):
        with capture_stdio() as stdio:
            in_, out, err = stdio
            args = ['server.json', 'c']
            ctrl.main(args, _bot_cls=FakeBot, _cmd_cls=FakeCmd)
            self.assertEqual(out.items[0], 'Client config file `c` not found.')

    def test_main_console(self):
        tf = tempfile.NamedTemporaryFile()
        args = [tf.name, tf.name]
        tf.write(b'test')
        tf.flush()
        ctrl.main(args, _bot_cls=FakeBot, _cmd_cls=FakeCmd)
        # workaround appended
        self.assertEqual(args[-1], 'console')

    def test_main_fg(self):
        tf = tempfile.NamedTemporaryFile()
        tf.write(b'test')
        tf.flush()
        args = [tf.name, tf.name, 'fg']
        result = ctrl.main(args, _bot_cls=FakeBot, _cmd_cls=FakeCmd)
        self.assertEqual(result, 'fg ')

    def test_main_generate_config(self):
        with capture_stdio() as stdio:
            in_, out, err = stdio
            args = ['--gen-config', 'server']
            self.assertRaises(SystemExit, ctrl.main, args,
                _bot_cls=FakeBot, _cmd_cls=FakeCmd)
            self.assertEqual(json.loads(out.items[0])['host'],
                'talk.example.com')

        with capture_stdio() as stdio:
            in_, out, err = stdio
            args = ['--gen-config', 'client']
            self.assertRaises(SystemExit, ctrl.main, args,
                _bot_cls=FakeBot, _cmd_cls=FakeCmd)
            self.assertTrue(isinstance(json.loads(out.items[0]), dict))

        with capture_stdio() as stdio:
            in_, out, err = stdio
            args = ['--gen-config', 'client_example']
            self.assertRaises(SystemExit, ctrl.main, args,
                _bot_cls=FakeBot, _cmd_cls=FakeCmd)
            self.assertTrue(isinstance(json.loads(out.items[0]), dict))

    def test_main_generate_config_invalid_id(self):
        with capture_stdio() as stdio:
            in_, out, err = stdio
            args = ['--gen-config', 'server_invalid']
            self.assertRaises(SystemExit, ctrl.main, args,
                _bot_cls=FakeBot, _cmd_cls=FakeCmd)
            self.assertRaises(ValueError, json.loads, out.items[0])

    def test_cmd(self):
        bot = FakeBot()
        cmd = ctrl.JibberCmd(bot)
        with capture_stdio() as stdio:
            cmd.do_debug(())

    def test_cmd_bot_debug(self):
        bot = FakeBot()
        cmd = ctrl.JibberCmd(bot)
        with capture_stdio('bot_test()\n') as stdio:
            in_, out, err = stdio
            cmd.do_debug(())
            self.assertEqual(out.items[1],
                "Test client ready; call client('Hello bot') to interact.")
            cmd.do_EOF(())

    def test_cmd_bot_debug_bot_test_no_double(self):
        bot = FakeBot()
        cmd = ctrl.JibberCmd(bot)
        client = None
        with capture_stdio('bot_test()\n') as stdio:
            in_, out, err = stdio
            cmd.do_debug(())
            client = bot.client

        with capture_stdio('bot_test()\n') as stdio:
            in_, out, err = stdio
            cmd.do_debug(())
            self.assertEqual(client, bot.client)
            self.assertEqual(out.items[1],
                "Error: Bot already has an active client.")
            cmd.do_EOF(())

    def test_cmd_bot_fg(self):
        bot = FakeBot()
        cmd = ctrl.JibberCmd(bot)
        cmd.timeout = 0
        with capture_stdio() as stdio:
            in_, out, err = stdio
            cmd.do_fg(())
            self.assertEqual(bot.connected, 1)
            self.assertEqual(bot.disconnected, 1)
            self.assertFalse('bot is dying in a fire, attempting to abort...'
                in out.items)

    def test_cmd_bot_fg_nope(self):
        bot = NotBot()
        cmd = ctrl.JibberCmd(bot)
        cmd.timeout = 0
        with capture_stdio() as stdio:
            in_, out, err = stdio
            cmd.do_fg(())
            self.assertEqual(bot.connected, 1)
            self.assertEqual(bot.disconnected, 1)
            self.assertTrue('bot is dying in a fire, attempting to abort...'
                in out.items)

    def test_cmd_bot_fg_kb(self):
        class KbFakeBot(FakeBot):
            def is_alive(self):
                raise KeyboardInterrupt

        bot = KbFakeBot()
        cmd = ctrl.JibberCmd(bot)
        cmd.timeout = 0
        with capture_stdio() as stdio:
            in_, out, err = stdio
            cmd.do_fg(())
            self.assertEqual(bot.connected, 1)
            self.assertEqual(bot.disconnected, 1)
            self.assertFalse('bot is dying in a fire, attempting to abort...'
                in out.items)
