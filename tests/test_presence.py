from unittest import TestCase

from mtj.jibber.presence import Muc
from mtj.jibber.jabber import MucChatBot
from mtj.jibber.testing.client import TestClient
from mtj.jibber.testing.client import TestMuc
from mtj.jibber.testing.client import Jid


class PresenceTestCase(TestCase):

    def setUp(self):
        bot = MucChatBot()
        bot.jid = 'bot@example.com'
        bot.client = TestClient()
        bot.nickname = 'testbot'
        bot.muc = TestMuc()
        self.bot = bot

    def test_handle_rejoin_success(self):
        handler = Muc()
        handler.auto_rejoin({
            'to': 'bot@example.com',
            'from': Jid('room', 'room@example.com', 'testbot')
        }, self.bot)

        self.assertEqual(self.bot.muc.joined_rooms,
            [('testbot', 'room@example.com')])

    def test_handle_rejoin_unrelated(self):
        handler = Muc()
        handler.auto_rejoin({
            'to': 'bot@example.com',
            'from': Jid('room', 'room@example.com', 'testbot2') # different
        }, self.bot)

        self.assertEqual(self.bot.muc.joined_rooms, [])

    def test_handle_rejoin_not_bot(self):
        handler = Muc()
        handler.auto_rejoin({
            'to': 'some_user@example.com',
            'from': Jid('room', 'room@example.com', 'some user')
        }, self.bot)

        self.assertEqual(self.bot.muc.joined_rooms, [])

    def test_handle_rejoin_scheduled(self):
        handler = Muc(auto_rejoin_timeout=10)
        handler.auto_rejoin({
            'to': 'bot@example.com',
            'from': Jid('room', 'room@example.com', 'testbot')
        }, self.bot)

        self.assertEqual(self.bot.muc.joined_rooms, [])
        self.assertIn('Rejoin room@example.com', self.bot.client.schedules)

        # no exceptions
        handler.auto_rejoin({
            'to': 'bot@example.com',
            'from': Jid('room', 'room@example.com', 'testbot')
        }, self.bot)
        self.assertEqual(self.bot.muc.joined_rooms, [])

    def test_handle_greeter_greet(self):
        handler = Muc(greet=['room@example.com/Test Mucnick'])
        handler.greeter({
            'to': 'bot@example.com',
            'from': Jid('room', 'room@example.com', 'Test Mucnick'),
            'muc': {
                'role': 'participant',
            }
        }, self.bot)

        self.assertEqual(self.bot.client.full_sent, [{
            'mbody': 'Hello Test Mucnick',
            'mhtml': None,
            'mtype': 'groupchat',
            'mto': 'room@example.com',
        }])

    def test_handle_greeter_no_greet(self):
        handler = Muc(greet=['room@example.com/Test Mucnick'])
        handler.greeter({
            'to': 'bot@example.com',
            'from': Jid('room', 'room@example.com', 'Wrong nick'),
            'muc': {
                'role': 'participant',
            }
        }, self.bot)

        self.assertEqual(self.bot.client.full_sent, [])

    def test_handle_greeter_wrong_role(self):
        handler = Muc(greet=['room@example.com/Test Mucnick'])
        handler.greeter({
            'to': 'bot@example.com',
            'from': Jid('room', 'room@example.com', 'Test Mucnick'),
            'muc': {
                'role': 'what?',
            }
        }, self.bot)

        self.assertEqual(self.bot.client.full_sent, [])
