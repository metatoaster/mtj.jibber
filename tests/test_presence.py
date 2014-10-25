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
            'from': Jid('room', 'room@example.com')
        }, self.bot)

        self.assertEqual(self.bot.muc.rooms, [('testbot', 'room@example.com')])

    def test_handle_rejoin_not_bot(self):
        handler = Muc()
        handler.auto_rejoin({
            'to': 'some_user@example.com',
            'from': Jid('room', 'room@example.com')
        }, self.bot)

        self.assertEqual(self.bot.muc.rooms, [])

    def test_handle_rejoin_scheduled(self):
        handler = Muc(auto_rejoin_timeout=10)
        handler.auto_rejoin({
            'to': 'bot@example.com',
            'from': Jid('room', 'room@example.com')
        }, self.bot)

        self.assertEqual(self.bot.muc.rooms, [])
        self.assertIn('Rejoin room@example.com', self.bot.client.schedules)

        # no exceptions
        handler.auto_rejoin({
            'to': 'bot@example.com',
            'from': Jid('room', 'room@example.com')
        }, self.bot)
        self.assertEqual(self.bot.muc.rooms, [])
