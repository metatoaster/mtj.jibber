from unittest import TestCase

from mtj.jibber.jabber import MucChatBot
from mtj.jibber.testing.client import TestClient


class TestClientTestCase(TestCase):

    def setUp(self):
        self.test_package = 'mtj.jibber.testing.command.GreeterCommand'
        self.commands = [
            ['^%(nickname)s: hi', 'say_hi'],
            ['^%(nickname)s: hello', 'say_hello_all'],
        ]
        self.kwargs = {}
        self.config = {
            'nickname': 'testbot',
            'commands_max_match': 1,
            'packages': [
                {
                    'kwargs': self.kwargs,
                    'package': 'mtj.jibber.testing.command.GreeterCommand',
                    'commands': self.commands,
                },

            ]
        }

    def tearDown(self):
        pass

    def test_muc_bot_success_general(self):
        bot = MucChatBot()
        client = TestClient()

        bot.client = client
        bot.config = self.config
        bot.setup_client()

        client('testbot: hi')
        self.assertEqual(bot.client.sent, ['hi Tester'])

        bot.disconnect()
