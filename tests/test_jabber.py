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
        self.test_package = 'mtj.jibber.testing.command.GreeterCommand'
        self.private_commands = [
            ['^(.*)$', 'pm_reply'],
        ]
        self.commands = [
            ['^%(nickname)s: hi', 'say_hi'],
            ['^%(nickname)s: legacy', 'say_legacy_hi'],
            ['^%(nickname)s: hello', 'say_hello_all'],
        ]
        self.schedule = [
            {'seconds': 'abc', 'method': 'say_hello_all'},
            {'seconds': (7200, 14400), 'method': 'say_hello_all'},
            {'seconds': 1800, 'method': 'report_time'},
        ]
        self.listeners = [
            'listener',
        ]
        self.commentators = []
        self.kwargs = {}
        self.rebuild_config()

    def rebuild_config(self):
        self.config = {
            'nickname': 'testbot',
            'commands_max_match': 1,
            'packages': [
                {
                    'kwargs': self.kwargs,
                    'package': self.test_package,
                    'private_commands': self.private_commands,
                    'commands': self.commands,
                    'commentators': self.commentators,
                    'timers': [
                        {
                            'mtype': 'groupchat',
                            'mto': 'testing@chat.example.com',
                            'schedule': self.schedule,
                        },
                    ],
                    'listeners': self.listeners,

                },

            ]
        }

    def tearDown(self):
        pass

    def mk_default_bot(self, config=None, nickname='testbot'):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = nickname
        bot.config = config or self.config
        bot.setup_packages()
        return bot

    def add_command(self, cmd):
        self.commands.append(cmd)

    def add_kwargs(self, kwargs):
        self.kwargs.clear()
        self.kwargs.update(kwargs)

    def test_send_message_text(self):
        bot = self.mk_default_bot()
        bot.send_message(raw='test', mto='')
        self.assertEqual(bot.client.msg[-1],
            {'mbody': 'test', 'mhtml': None, 'mto': '',})

    def test_send_message_html(self):
        bot = self.mk_default_bot()
        bot.send_message(raw='<p>test</p>', mto='')
        self.assertEqual(bot.client.msg[-1],
            {'mbody': 'test', 'mhtml': '<p>test</p>', 'mto': '',})

        bot.send_message(raw='<html>test</html>', mto='')
        self.assertEqual(bot.client.msg[-1],
            {'mbody': 'test', 'mhtml': '<html>test</html>', 'mto': '',})

    def test_send_package_method_text(self):
        bot = self.mk_default_bot()
        bot.send_package_method(
            'mtj.jibber.testing.command.GreeterCommand', 'say_hello_all',
             mto='test@chat.example.com')
        self.assertEqual(bot.client.msg, [
            {'mbody': 'hello all', 'mto': 'test@chat.example.com',
            'mhtml': None},
        ])

    def test_send_package_method_dict(self):
        bot = self.mk_default_bot()
        bot.send_package_method(
            'mtj.jibber.testing.command.GreeterCommand', 'to_one_target',
             msg={'mucroom': 'test@chat.example.com'})
        self.assertEqual(bot.client.msg, [
            {'mto': 'test@chat.example.com', 'mbody': 'hello target',
            'mhtml': None},
        ])

    def test_send_package_method_list_dict(self):
        bot = self.mk_default_bot()
        bot.send_package_method(
            'mtj.jibber.testing.command.GreeterCommand', 'to_multi_target',
             mto='test@chat.example.com')
        self.assertEqual(bot.client.msg, [
            {'mto': 'beacon@example.com', 'mbody': 'test123', 'mhtml': None},
            {'mto': 'answer@example.com', 'mbody': '42', 'mhtml': None},
        ])

    def test_send_package_method_list_trap(self):
        bot = self.mk_default_bot()
        bot.send_package_method(
            'mtj.jibber.testing.command.GreeterCommand', 'to_trap',
             mto='test@chat.example.com')
        self.assertEqual(bot.client.msg, [
            {'mto': 'trap@example.com', 'mbody': 'pretrap', 'mhtml': None},
            {'mto': 'trap@example.com', 'mbody': 'posttrap', 'mhtml': None},
        ])

    def test_send_package_method_error(self):
        class E(object):
            def fail(self):
                raise NotImplementedError
        bot = self.mk_default_bot()
        bot.objects['error'] = E()
        bot.send_package_method('error', 'fail')
        # error should be logged
        self.assertEqual(bot.client.msg, [])

        # it is possible to remove objects completely while inside the
        # debugger, in that case the failure should be logged and fail
        # silently.
        result = bot.send_package_method('error', 'failure')
        self.assertIsNone(result)

    def test_setup_commands(self):
        bot = MucChatBot()
        bot.nickname = 'test'
        bot.commands = []
        marker = object()

        # null command
        bot.setup_commands(marker, commands=None)
        self.assertEqual(bot.commands, [])

        # bad commands
        bot.setup_commands(object(), commands=[
            [], # not enough values
            ['(', 'command'],  # bad regex
        ])
        self.assertEqual(bot.commands, [])

        # bad commands
        bot.setup_commands(object(), commands=[
            ['(test)', 'command'],
        ])
        self.assertEqual(len(bot.commands), 1)

    def test_setup_private_commands(self):
        bot = MucChatBot()
        bot.nickname = 'test'
        bot.private_commands = []
        marker = object()

        # null command
        bot.setup_private_commands(marker, private_commands=None)
        self.assertEqual(bot.private_commands, [])

        # bad commands
        bot.setup_private_commands(object(), private_commands=[
            [], # not enough values
            ['(', 'command'],  # bad regex
        ])
        self.assertEqual(bot.private_commands, [])

        # bad commands
        bot.setup_private_commands(object(), private_commands=[
            ['(test)', 'command'],
        ])
        self.assertEqual(len(bot.private_commands), 1)

    def test_setup_package_alias(self):
        # ensure the default config in this test is what we expect
        config = {'nickname': 'testbot', 'packages': [
            {'package': self.test_package,
                'kwargs': {'a': 'b'},
                'alias': 'instance_a',
            },
            {'package': self.test_package,
                'kwargs': {'c': 'd'},
                'alias': 'instance_b',
            },
        ]}
        bot = self.mk_default_bot(config=config)
        self.assertEqual(sorted(bot.objects.keys()),
            ['instance_a', 'instance_b'])
        self.assertEqual(bot.objects['instance_a'].kw, {'a': 'b'})
        self.assertEqual(bot.objects['instance_b'].kw, {'c': 'd'})

    def test_setup_package_method_send_as_alias(self):
        # ensure the default config in this test is what we expect
        self.assertEqual(self.config['packages'][0]['package'],
            'mtj.jibber.testing.command.GreeterCommand')
        self.config['packages'][0]['alias'] = 'hello'
        bot = self.mk_default_bot()
        bot.send_package_method('hello', 'say_hello_all',
             mto='test@chat.example.com')
        self.assertEqual(bot.client.msg, [
            {'mbody': 'hello all', 'mto': 'test@chat.example.com',
            'mhtml': None},
        ])

    def test_muc_bot_success_command(self):
        bot = self.mk_default_bot()
        self.assertEqual(bot.objects[self.test_package].bot, bot)
        bot.run_command({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'testbot: hi',
        })
        self.assertEqual(bot.client.msg[0]['mtype'], 'groupchat')
        self.assertEqual(bot.client.msg[0]['mbody'], 'hi tester')

    def test_muc_bot_legacy_command(self):
        # TODO until the bot argument is required...
        bot = self.mk_default_bot()
        bot.run_command({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'testbot: legacy',
        })
        self.assertEqual(bot.client.msg[0]['mtype'], 'groupchat')
        self.assertEqual(bot.client.msg[0]['mbody'], 'hi tester')

    def test_muc_bot_success_command_ignore_self(self):
        bot = self.mk_default_bot()
        self.assertEqual(bot.objects[self.test_package].bot, bot)
        bot.run_command({
            'mucnick': 'testbot',
            'mucroom': 'testroom',
            'body': 'testbot: hi',
        })
        self.assertEqual(bot.client.msg, [])

    def test_muc_bot_fail_not_command(self):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = 'testbot'
        self.config['packages'][0]['package'] = \
            'mtj.jibber.testing.command.Greeter'

        bot.config = self.config
        bot.setup_packages()

        bot.run_command({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'testbot: hi',
        })

        self.assertEqual(len(bot.client.msg), 0)

    def test_muc_bot_success_private_command(self):
        bot = self.mk_default_bot()
        # the event handler will send these
        bot.run_private_command({
            'type': 'groupchat',
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'hi',
        })
        self.assertEqual(len(bot.client.msg), 0)

        # the event handler will send these
        bot.run_private_command({
            'type': 'chat',
            'body': 'hi',
            'from': 'nobody@example.com',
        })
        self.assertEqual(bot.client.msg[0]['mbody'], 'You said: hi')

    def test_muc_bot_success_private_command_no_match(self):
        self.private_commands = [['^dddd$', 'pm_reply']]
        self.rebuild_config()
        bot = self.mk_default_bot()
        bot.run_private_command({
            'type': 'chat',
            'body': 'hi',
            'from': 'nobody@example.com',
        })
        self.assertEqual(len(bot.client.msg), 0)

    def test_muc_bot_success_private_command_none(self):
        self.private_commands = []
        self.rebuild_config()
        bot = self.mk_default_bot()
        bot.run_private_command({
            'type': 'chat',
            'body': 'hi',
            'from': 'nobody@example.com',
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
        bot.setup_packages()

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
        bot.setup_packages()

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
        bot.setup_packages()

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
        bot.setup_packages()

        self.assertEqual(bot.timers, {
            ('mtj.jibber.testing.command.GreeterCommand', 'say_hello_all'):
                ((7200, 14400), {
                    'mtype': 'groupchat', 'mto': 'testing@chat.example.com',
                }),
            ('mtj.jibber.testing.command.GreeterCommand', 'report_time'):
                (1800, {
                    'mtype': 'groupchat', 'mto': 'testing@chat.example.com',
                })
        })

        self.assertEqual(sorted(bot.client.schedules), [
            "('mtj.jibber.testing.command.GreeterCommand', 'report_time')",
            "('mtj.jibber.testing.command.GreeterCommand', 'say_hello_all')",
        ])

        self.assertEqual(len(bot.client.scheduler), 2)
        self.assertEqual(len(bot.client.schedules), 2)

        bot.send_package_method(
            'mtj.jibber.testing.command.GreeterCommand', 'say_hello_all',
             mto='test@chat.example.com')

        self.assertEqual(len(bot.client.scheduler), 2)
        self.assertEqual(len(bot.client.schedules), 3)

    def test_muc_bot_timers_multi(self):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = 'testbot'
        bot.config = {'nickname': 'testbot', 'packages': [
            {'package': self.test_package,
                'kwargs': {'a': 'b'},
                'alias': 'instance_a',
                'timers': [
                    {
                        'mtype': 'groupchat',
                        'mto': 'testing@chat.example.com',
                        'schedule': self.schedule,
                    },
                ],
            },
            {'package': self.test_package,
                'kwargs': {'c': 'd'},
                'alias': 'instance_b',
                'timers': [
                    {
                        'mtype': 'groupchat',
                        'mto': 'testing@chat.example.com',
                        'schedule': self.schedule,
                    },
                ],
            },
        ]}
        bot.setup_packages()

        self.assertEqual(bot.timers, {
            ('instance_a', 'say_hello_all'):
                ((7200, 14400), {
                    'mtype': 'groupchat', 'mto': 'testing@chat.example.com',
                }),
            ('instance_a', 'report_time'):
                (1800, {
                    'mtype': 'groupchat', 'mto': 'testing@chat.example.com',
                }),
            ('instance_b', 'say_hello_all'):
                ((7200, 14400), {
                    'mtype': 'groupchat', 'mto': 'testing@chat.example.com',
                }),
            ('instance_b', 'report_time'):
                (1800, {
                    'mtype': 'groupchat', 'mto': 'testing@chat.example.com',
                })
        })

        self.assertEqual(sorted(bot.client.schedules), [
            "('instance_a', 'report_time')",
            "('instance_a', 'say_hello_all')",
            "('instance_b', 'report_time')",
            "('instance_b', 'say_hello_all')",
        ])

    def test_muc_bot_timers_clear(self):
        bot = self.mk_default_bot()
        self.assertEqual(len(bot.timers), 2)
        self.assertEqual(len(bot.client.scheduler), 2)
        bot.clear_timers()

        self.assertEqual(len(bot.timers), 0)
        self.assertEqual(len(bot.client.scheduler), 0)

    def test_muc_bot_timers_clear_failsafe(self):
        bot = self.mk_default_bot()
        # force in a broken timer.
        bot.timers[('mtj.jibber.testing.command.GreeterCommand', 'dummy')] = \
            (1800, {'mtype': 'groupchat', 'mto': 'testing@chat.example.com',})

        # should still clear.
        bot.clear_timers()
        self.assertEqual(len(bot.timers), 0)
        self.assertEqual(len(bot.client.scheduler), 0)

    def test_muc_bot_listeners_null(self):
        bot = MucChatBot()
        bot.client = TestClient()
        bot.nickname = 'testbot'
        bot.config = {
            'nickname': 'testbot',
            'commands_max_match': 1,
            'packages': [
                {
                    'kwargs': self.kwargs,
                    'package': 'mtj.jibber.testing.command.GreeterCommand',
                    'commands': self.commands,
                    'listeners': [
                    ]
                },
            ]
        }
        bot.setup_packages()
        self.assertEqual(bot.listeners, [])

        kw = {
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'print',
        }
        bot.run_listener(kw)
        self.assertEqual(bot.objects[self.test_package].listened, [])

    def test_muc_bot_listeners(self):
        bot = self.mk_default_bot()
        self.assertNotEqual(bot.listeners, [])
        kw = {
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'print',
        }
        bot.run_listener(kw)
        self.assertEqual(bot.objects[self.test_package].listened, [kw])
        kw2 = {
            'mucnick': 'testbot',
            'mucroom': 'testroom',
            'body': 'print',
        }
        bot.run_listener(kw2)
        self.assertEqual(bot.objects[self.test_package].listened, [kw])

    def test_muc_bot_listener_error(self):
        class E(object):
            def fail(self):
                raise NotImplementedError
        bot = self.mk_default_bot()
        bot.objects['error'] = E()
        bot.listeners.append(('error', 'fail'))
        kw = {'mucnick': 'tester', 'mucroom': 'testroom', 'body': 'print'}
        bot.run_listener(kw)
        # error should be logged
        self.assertEqual(bot.objects[self.test_package].listened, [kw])

    def test_muc_bot_commentator(self):
        self.commentators.append(['.*', 'repeat_you'])
        bot = self.mk_default_bot()

        bot.run_commentator({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'hello you',
        })

        self.assertEqual(len(bot.client.msg), 1)
        self.assertEqual(bot.client.msg[0]['mbody'], "hello you")
        self.assertEqual(list(bot.commentary), ["hello you"])

        # the above would have got the server to do this again.
        bot.run_commentator({
            'mucnick': 'testbot',
            'mucroom': 'testroom',
            'body': 'hello you',
        })

        # should be ignored.
        self.assertEqual(len(bot.client.msg), 1)

        # Someone else can of course say the same thing again and the
        # bot will reply...
        bot.run_commentator({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'hello you',
        })

        self.assertEqual(len(bot.client.msg), 2)
        self.assertEqual(list(bot.commentary), ["hello you", "hello you"])

        # Say something different...
        # bot will reply...
        bot.run_commentator({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'bye.',
        })

        self.assertEqual(len(bot.client.msg), 3)
        self.assertEqual(list(bot.commentary), ["hello you", "bye."])

        # Maybe a timer on that bomb in the bot ran out...
        bot.run_commentator({
            'mucnick': 'testbot',
            'mucroom': 'testroom',
            'body': 'BOOM',
        })

        self.assertEqual(len(bot.client.msg), 4)
        # he commented.
        self.assertEqual(list(bot.commentary), ["bye.", "BOOM"])
        # would have repeated himself but we already tested that.

    def test_muc_bot_commentator_explicit(self):
        self.commentators.append(['repeat: ', 'repeat_you'])
        bot = self.mk_default_bot()

        bot.run_commentator({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'hello you',
        })
        self.assertEqual(len(bot.client.msg), 0)

        bot.run_commentator({
            'mucnick': 'tester',
            'mucroom': 'testroom',
            'body': 'repeat: hello you',
        })
        self.assertEqual(len(bot.client.msg), 1)

    def test_muc_bot_commentary_qsize_fail(self):
        self.config['commentary_qsize'] = 0
        self.assertRaises(ValueError, self.mk_default_bot)

    def test_run_timer(self):
        bot = self.mk_default_bot()
        def testfunc(s, c):
            return s * c
        result = bot.run_timer(testfunc, ('s',), {'c': 2})
        self.assertEqual(result, 'ss')
