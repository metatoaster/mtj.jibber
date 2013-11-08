from unittest import TestCase

from mtj.jibber.core import BotCore
from mtj.jibber.core import MucBotCore
from mtj.jibber.core import Command
from mtj.jibber.testing.client import TestClient


class BotTestCase(TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_bot_core_base(self):
        bot = BotCore()
        self.assertTrue(bot.jid is None)

    def test_bot_core_s_config(self):
        bot = BotCore(s_config='''{
            "jid": "test@example.com",
            "password": "password"
        }''')

        self.assertEqual(bot.jid, 'test@example.com')
        self.assertEqual(bot.password, 'password')
        self.assertEqual(bot.host, None)
        self.assertEqual(bot.port, 5222)

    def test_bot_core_c_config(self):
        config = '{"a_setting": "value"}'
        bot = BotCore(c_config=config)
        self.assertEqual(bot.config, {'a_setting': 'value'})
        config = '{"a_setting": "value2", "b": "number"}'
        bot.load_client_config(config)
        self.assertEqual(bot.config, {'a_setting': 'value2', 'b': 'number'})

    def test_bot_core_server_config(self):
        bot = BotCore()
        bot.load_server_config(
            '{"jid": "test@example.com/res", "password": "passwd"}')
        self.assertEqual(bot.jid, 'test@example.com/res')
        self.assertEqual(bot.password, 'passwd')
        self.assertEqual(bot.address, None)

        bot.load_server_config(
            '{"jid": "test@example.com/res", "password": "passwd", '
            '"host": "talk.example.com"}')
        self.assertEqual(bot.address, ('talk.example.com', 5222))

        bot.load_server_config(
            '{"jid": "test@example.com/res", "password": "passwd", '
            '"host": "talk.example.com", "port": "5222"}')
        self.assertEqual(bot.address, ('talk.example.com', 5222))

        bot.load_server_config(
            '{"jid": "test@example.com/res", "password": "passwd", '
            '"host": "talk.example.com", "port": 52222}')
        self.assertEqual(bot.address, ('talk.example.com', 52222))

    def test_bot_client_config(self):
        bot = BotCore()
        bot.load_client_config('{"test": "1234"}')
        self.assertEqual(bot.config, {'test': '1234'})
        bot.load_client_config('{"test": "12345"}')
        self.assertEqual(bot.config, {'test': '12345'})
        bot.load_client_config('{"key": ["a", "b"]}')
        self.assertEqual(bot.config, {'test': '12345', 'key': ['a', 'b']})

    def test_connect(self):
        class TestClient(object):
            def __init__(self, *a, **kw):
                self.init = (a, kw)
            def connect(self, *a, **kw):
                self.a = a
                self.kw = kw
            def process(self, *a, **kw):
                pass
            def disconnect(self, *a, **kw):
                pass

        bot = BotCore()
        bot._client_cls = TestClient
        bot.load_server_config(
            '{"jid": "test@example.com/res", "password": "passwd"}')
        self.assertTrue(bot.client is None)

        bot.connect()
        self.assertFalse(bot.client is None)

        client = bot.client
        bot.connect()
        self.assertEqual(client, bot.client)

        bot.disconnect()
        self.assertTrue(bot.client is None)

        bot.disconnect()
        self.assertTrue(bot.client is None)

    def test_setup_methods(self):

        def dummy():
            pass

        bot = BotCore()
        client = TestClient()
        bot.setup_plugins(client, ['test', 'one'])
        self.assertEqual(client.plugins, ['test', 'one'])

        bot.setup_events(client, [('setup', dummy)])
        self.assertEqual(client.events, [('setup', dummy)])


class MucBotTestCase(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_muc_core_base(self):
        bot = MucBotCore()
        bot.make_client()
        self.assertTrue(bot.jid is None)
        self.assertFalse(bot.muc is None)

    def test_join_rooms(self):
        class TestMuc(object):
            rooms = []
            def joinMUC(self, room, nickname, **kw):
                self.rooms.append((nickname, room))

        bot = MucBotCore()
        bot.muc = TestMuc()
        bot.client = TestClient()

        bot.config = {
            'nickname': 'tester',
            'rooms': ['testroom@chat.example.com', 'tester@chat.example.com'],
        }

        bot.join_rooms({})
        self.assertEqual(TestMuc.rooms, [
            ('tester', 'testroom@chat.example.com'),
            ('tester', 'tester@chat.example.com'),
        ])


class CommandTestCase(TestCase):

    def test_command(self):
        c = Command()
