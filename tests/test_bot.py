from unittest import TestCase

import re

from sleekxmpp.xmlstream import ET

from mtj.jibber.jabber import MucChatBot
from mtj.jibber.bot import MucAdmin
from mtj.jibber.bot import RussianRoulette

from mtj.jibber.testing.client import TestClient
from mtj.jibber.testing.client import TestMuc
from mtj.jibber.testing.client import Jid


def mk_default_bot(config=None, nickname='testbot'):
    bot = MucChatBot()
    bot.client = TestClient()
    bot.nickname = nickname
    bot.muc = TestMuc()
    bot.muc.rooms = {}
    return bot


class MucAdminTestCase(TestCase):

    def setUp(self):
        self.muc_admin = MucAdmin()

    def tearDown(self):
        pass

    def mk_default_bot(self, config=None, nickname='testbot'):
        return mk_default_bot(config, nickname)

    def test_admin_kick_nickname_bot_not_in_room(self):
        bot = self.mk_default_bot()
        match = re.search('(?P<victim>.*)', 'a_victim')
        msg = {
            'from': Jid('room', 'room@example.com', 'kicker')
        }
        # nothing should happen
        self.muc_admin.admin_kick_nickname(msg, match, bot)

    def test_admin_kick_nickname_bot_not_a_mod(self):
        bot = self.mk_default_bot()
        bot.muc.rooms = {
            'room@example.com': {
                'testbot': {'role': 'participant',},
                'kicker': {'role': 'participant',},
            },
        }
        match = re.search('(?P<victim>.*)', 'a_victim')
        msg = {
            'from': Jid('room', 'room@example.com', 'kicker')
        }
        self.muc_admin.admin_kick_nickname(msg, match, bot)
        self.assertEqual(len(bot.client.raw), 0)

    def test_admin_kick_nickname_kicker_missing(self):
        bot = self.mk_default_bot()
        bot.muc.rooms = {
            'room@example.com': {
                'testbot': {'role': 'moderator',},
            },
        }
        match = re.search('(?P<victim>.*)', 'a_victim')
        msg = {
            'from': Jid('room', 'room@example.com', 'kicker')
        }
        self.muc_admin.admin_kick_nickname(msg, match, bot)
        self.assertEqual(len(bot.client.raw), 0)

    def test_admin_kick_nickname_kicker_kicked(self):
        bot = self.mk_default_bot()
        bot.muc.rooms = {
            'room@example.com': {
                'testbot': {'role': 'moderator',},
                'kicker': {'role': 'participant',},
            },
        }
        match = re.search('(?P<victim>.*)', 'a_victim')
        msg = {
            'from': Jid('room', 'room@example.com', 'kicker')
        }
        self.muc_admin.admin_kick_nickname(msg, match, bot)
        self.assertEqual(len(bot.client.raw), 1)
        self.assertEqual(bot.client.raw[0]['to'], 'room@example.com')

    def test_admin_kick_nickname_victim_missing(self):
        bot = self.mk_default_bot()
        bot.muc.rooms = {
            'room@example.com': {
                'testbot': {'role': 'moderator',},
                'kicker': {'role': 'moderator',},
            },
        }
        match = re.search('(?P<victim>.*)', 'a_victim')
        msg = {
            'from': Jid('room', 'room@example.com', 'kicker')
        }
        self.muc_admin.admin_kick_nickname(msg, match, bot)
        self.assertEqual(len(bot.client.raw), 0)

    def test_admin_kick_nickname_victim_kicked(self):
        bot = self.mk_default_bot()
        bot.muc.rooms = {
            'room@example.com': {
                'testbot': {'role': 'moderator',},
                'kicker': {'role': 'moderator',},
                'a_victim': {'role': 'participant',},
            },
        }
        match = re.search('(?P<victim>.*)', 'a_victim')
        msg = {
            'mucnick': 'kicker',
            'from': Jid('room', 'room@example.com', 'kicker'),
        }
        result = self.muc_admin.admin_kick_nickname(msg, match, bot)
        self.assertEqual(len(bot.client.raw), 1)
        self.assertEqual(result,
            'kicker: Okay, I have kicked a_victim for you.')


class TestRussianRoulette(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_survive(self):
        rr = RussianRoulette(bullets=0, slots=6)
        msg = {'mucnick': 'player',}
        result = rr.play(msg, None, None)
        self.assertEqual(result,
            '*click*... it appears player lives another day.')

    def test_death(self):
        rr = RussianRoulette(bullets=6, slots=6)
        bot = MucChatBot()
        bot.client = TestClient()
        msg = {
            'mucnick': 'player',
            'from': Jid('room', 'room@example.com', 'player')
        }

        result = rr.play(msg, None, bot)
        self.assertIsNone(result)
        self.assertEqual(len(bot.client.raw), 1)
