from unittest import TestCase

from mtj.jibber.jabber import MucChatBot


class TestClient(object):
    def __init__(self):
        self.msg = []
        self.schedules = []  # for checking all added timers
        self.scheduler = []  # for mimicking the remove method
    def send_message(self, *a, **kw):
        self.msg.append(kw)
    def schedule(self, name, seconds, *a, **kw):
        self.schedules.append(name)
        self.scheduler.append(name)


class MucBotTestCase(TestCase):

    def setUp(self):
        self.commands = [
            ['^%(nickname)s: hi', 'say_hi'],
            ['^%(nickname)s: hello', 'say_hello_all'],
        ]
        self.schedule = [
            {'seconds': 7200, 'method': 'say_hello_all'},
            {'seconds': 1800, 'method': 'report_time'},
        ]
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

                {
                    'kwargs': self.kwargs,
                    'package': 'mtj.jibber.testing.command.GreeterCommand',
                    'timers': [
                        {
                            'mtype': 'groupchat',
                            'mto': 'testing@chat.example.com',
                            'schedule': self.schedule,
                        },
                    ],

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

    def test_muc_bot_timers(self):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = 'testbot'
        bot.config = self.config
        bot.setup_commands()

        self.assertEqual(bot.timers, {
            ('mtj.jibber.testing.command.GreeterCommand', 'say_hello_all'):
                (7200, {
                    'mtype': 'groupchat', 'mto': 'testing@chat.example.com',
                }),
            ('mtj.jibber.testing.command.GreeterCommand', 'report_time'):
                (1800, {
                    'mtype': 'groupchat', 'mto': 'testing@chat.example.com',
                })
        })

        self.assertEqual(bot.client.schedules, [
            "('mtj.jibber.testing.command.GreeterCommand', 'say_hello_all')",
            "('mtj.jibber.testing.command.GreeterCommand', 'report_time')",
        ])

        self.assertEqual(len(bot.client.scheduler), 2)
        self.assertEqual(len(bot.client.schedules), 2)

        bot.send_package_method(
            'mtj.jibber.testing.command.GreeterCommand', 'say_hello_all',
             mto='test@chat.example.com')

        self.assertEqual(len(bot.client.scheduler), 2)
        self.assertEqual(len(bot.client.schedules), 3)
