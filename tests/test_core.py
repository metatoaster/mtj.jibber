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
