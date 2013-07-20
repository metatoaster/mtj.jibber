from unittest import TestCase

from mtj.jibber.jabber import MucChatBot


class TestClient(object):
    def __init__(self):
        self.msg = []
    def send_message(self, *a, **kw):
        self.msg.append(kw)


class MucBotTestCase(TestCase):

    def setUp(self):
        self.commands = [['^%(nickname)s: hi', 'say_hi']]
        self.kwargs = {}
        self.config = {
            'nickname': 'testbot',
            'commands_max_match': 1,
            'commands_packages': [
                {
                    'kwargs': self.kwargs,
                    'package': 'mtj.jibber.testing.command.GreeterCommand',
                    'commands': self.commands,
                },
            ]
        }

    def teatDown(self):
        pass

    def add_command(self, cmd):
        self.commands.append(cmd)

    def add_kwargs(self, kwargs):
        self.kwargs.clear()
        self.kwargs.update(kwargs)

    def test_muc_bot_success_general(self):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = 'testbot'
        bot.config = self.config

        bot.setup_commands()

        bot.run_command({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'testbot: hi',
        })

        self.assertEqual(bot.client.msg[0]['mtype'], 'groupchat')
        self.assertEqual(bot.client.msg[0]['mbody'], 'hi tester')

    def test_muc_bot_fail_not_command(self):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = 'testbot'
        self.config['commands_packages'][0]['package'] = \
            'mtj.jibber.testing.command.Greeter'

        bot.config = self.config
        bot.setup_commands()

        bot.run_command({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'testbot: hi',
        })

        self.assertEqual(len(bot.client.msg), 0)

    def test_muc_bot_construct(self):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = 'testbot'
        bot.config = self.config
        self.add_kwargs({'arg1': 'test'})
        self.add_command(['printa', 'say_a'])
        self.add_command(['printkw', 'say_kw'])
        bot.setup_commands()

        bot.run_command({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'printa',
        })

        bot.run_command({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'printkw',
        })

        self.assertEqual(bot.client.msg[0]['mbody'], "()")
        self.assertEqual(bot.client.msg[1]['mbody'], "{'arg1': 'test'}")

    def test_muc_bot_single(self):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = 'testbot'
        bot.config = self.config
        self.add_kwargs({'arg1': 'test'})
        self.add_command(['print', 'say_a'])
        self.add_command(['print', 'say_kw'])
        bot.setup_commands()

        self.assertEqual(bot.commands_max_match, 1)

        bot.run_command({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'print',
        })

        self.assertEqual(len(bot.client.msg), 1)

    def test_muc_bot_multimatch(self):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = 'testbot'
        bot.config = self.config
        self.add_kwargs({'arg1': 'test'})
        self.add_command(['print', 'say_a'])
        self.add_command(['print', 'say_kw'])
        self.config['commands_max_match'] = 2
        bot.setup_commands()

        bot.run_command({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'print',
        })

        self.assertEqual(bot.client.msg[0]['mbody'], "()")
        self.assertEqual(bot.client.msg[1]['mbody'], "{'arg1': 'test'}")
