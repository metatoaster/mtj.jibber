from unittest import TestCase

from mtj.jibber.core import BotCore


class BotTestCase(TestCase):
    
    def setUp(self):
        pass

    def teatDown(self):
        pass

    def test_bot_core_base(self):
        bot = BotCore()
        self.assertTrue(bot.jid is None)

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
        class TestClient(object):
            def __init__(self, *a, **kw):
                self.plugins = []
                self.events = []
            def register_plugin(self, plugin):
                self.plugins.append(plugin)
            def add_event_handler(self, *a):
                self.events.append(a)

        def dummy():
            pass

        bot = BotCore()
        client = TestClient()
        bot.setup_plugins(client, ['test', 'one'])
        self.assertEqual(client.plugins, ['test', 'one'])

        bot.setup_events(client, [('setup', dummy)])
        self.assertEqual(client.events, [('setup', dummy)])
