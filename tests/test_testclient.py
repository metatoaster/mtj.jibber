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

    def test_client_schedule(self):
        client = TestClient()
        client.schedule('name', 'a', kw='kw')
        self.assertEqual(client.scheduler, [(('a',), {'kw': 'kw'})])
        self.assertEqual(list(client.schedules.keys()), ['name'])

        self.assertRaises(ValueError, client.schedule, 'name', 'a')

    def test_muc_bot_success_general(self):
        bot = MucChatBot()
        client = TestClient()

        bot.client = client
        bot.config = self.config
        bot.setup_client()

        client('testbot: hi')
        self.assertEqual(bot.client.sent, ['hi Tester'])

        client._clear()
        self.assertEqual(bot.client.sent, [])

        bot.disconnect()

    def test_muc_bot_no_double_setup_client(self):
        bot = MucChatBot()
        client = TestClient()

        bot.client = client
        bot.config = self.config

        # As the setup is faked..
        bot._muc_setup = True
        bot.setup_client()

        # would have not got the hooks to setup so that the triggers
        # would not be registered to allow the following.
        client('testbot: hi')
        self.assertNotEqual(bot.client.sent, ['hi Tester'])
