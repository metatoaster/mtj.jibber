from unittest import TestCase

import re
from time import time

from sleekxmpp.xmlstream import ET

from mtj.jibber.jabber import MucChatBot
import mtj.jibber.bot
from mtj.jibber.bot import MucAdmin
from mtj.jibber.bot import RussianRoulette
from mtj.jibber.bot import LastActivity

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
        self.assertIn('Only moderators may kick', str(bot.client.raw[0]))
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
        self.assertIn('Requested by moderator', str(bot.client.raw[0]))
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


class TestLastActivity(TestCase):

    def setUp(self):
        self.bot = mk_default_bot()
        self.bot.muc.rooms = {
            'room@example.com': {
                'A Test User': {
                    'jid': Jid('testbot1', 'testbot1@example.com', 'test1'),
                    'nick': 'A Test User',
                },
                'The Robot': {
                    'jid': Jid('rob', 'rob@example.com', 'bot'),
                    'nick': 'The Robot',
                },
                'Rob': {
                    'jid': Jid('rob', 'rob@example.com', 'home'),
                    'nick': 'Rob',
                },
            },
        }

        self.cmd = LastActivity()
        self._time = 1500000000

        mtj.jibber.bot.time = self.time

    def tearDown(self):
        mtj.jibber.bot.time = time

    def time(self):
        return self._time

    def test_add_all(self):
        room = 'room@example.com'
        jid = 'testbot@example.com'
        nick = 'Test Bot'
        timestamp = 1400000000

        self.cmd.add_all(room, jid, nick, timestamp)
        self.assertEqual(self.cmd.nicks, {(room, nick): (jid, timestamp)})
        self.assertEqual(self.cmd.jids, {(room, jid): (nick, timestamp)})

        timestamp = 1500000000

        self.cmd.add_all(room, jid, nick, timestamp)
        self.assertEqual(self.cmd.nicks, {(room, nick): (jid, timestamp)})
        self.assertEqual(self.cmd.jids, {(room, jid): (nick, timestamp)})

    def test_message_recorder(self):
        room = 'room@example.com'
        jid = 'rob@example.com'
        nick = 'Rob'
        timestamp = 1500000000
        msg = {'from': Jid('room', 'room@example.com', 'Rob')}
        self.cmd.message_recorder(msg, None, self.bot)
        self.assertEqual(self.cmd.nicks, {(room, nick): (jid, timestamp)})
        self.assertEqual(self.cmd.jids, {(room, jid): (nick, timestamp)})

        timestamp = self._time = 1600000000
        self.cmd.add_all(room, jid, nick, timestamp)
        self.cmd.message_recorder(msg, None, self.bot)
        self.assertEqual(self.cmd.nicks, {(room, nick): (jid, timestamp)})
        self.assertEqual(self.cmd.jids, {(room, jid): (nick, timestamp)})

    def test_roster_check(self):
        self.cmd.add_roster(None, None, self.bot)

        # nicks can be fairly deterministic
        self.assertEqual(self.cmd.nicks, {
            ('room@example.com', 'A Test User'):
                ('testbot1@example.com', 1500000000),
            ('room@example.com', 'The Robot'):
                ('rob@example.com', 1500000000),
            ('room@example.com', 'Rob'):
                ('rob@example.com', 1500000000),
        })
        # jids not so much, so we just check that there are 2.
        self.assertEqual(len(self.cmd.jids), 2)

    def test_report_nick_not_found(self):
        self.cmd.add_roster(None, None, self.bot)
        msg = {'from': Jid('room', 'room@example.com', 'Rob')}
        match = re.search('!seen (?P<nick>.*)', '!seen Nobody')
        result = self.cmd.report_nick(msg, match, self.bot)
        self.assertEqual(result,
            'Rob: Nobody has never been seen here before.')

    def test_report_nick_found(self):
        self.cmd.add_roster(None, None, self.bot)
        msg = {'from': Jid('room', 'room@example.com', 'Rob')}
        match = re.search('!seen (?P<nick>.*)', '!seen A Test User')
        result = self.cmd.report_nick(msg, match, self.bot)
        self.assertEqual(result,
            'Rob: A Test User is seen here right now.')

    def test_report_nick_last_seen(self):
        room = 'room@example.com'
        jid = 'lurker@example.com'
        nick = 'Lurker'
        timestamp = 1400000000

        self.cmd.add_all(room, jid, nick, timestamp)
        self.cmd.add_roster(None, None, self.bot)

        msg = {'from': Jid('room', 'room@example.com', 'Rob')}
        match = re.search('!seen (?P<nick>.*)', '!seen Lurker')
        result = self.cmd.report_nick(msg, match, self.bot)
        self.assertEqual(result,
            'Rob: Lurker was last seen 100000000 seconds ago.')

    def test_report_jid_not_found(self):
        self.cmd.add_roster(None, None, self.bot)
        msg = {'from': Jid('room', 'room@example.com', 'Rob')}
        match = re.search('!seen (?P<jid>.*)', '!seen nobody@example.com')
        result = self.cmd.report_jid(msg, match, self.bot)
        self.assertEqual(result,
            'Rob: nobody@example.com has never been seen here before.')

    def test_report_jid_found(self):
        self.cmd.add_roster(None, None, self.bot)
        msg = {'from': Jid('room', 'room@example.com', 'Rob')}
        match = re.search('!seen (?P<jid>.*)', '!seen testbot1@example.com')
        result = self.cmd.report_jid(msg, match, self.bot)
        self.assertEqual(result,
            'Rob: testbot1@example.com is seen here right now.')

    def test_report_jid_last_seen(self):
        room = 'room@example.com'
        jid = 'lurker@example.com'
        nick = 'Lurker'
        timestamp = 1400000000

        self.cmd.add_all(room, jid, nick, timestamp)
        self.cmd.add_roster(None, None, self.bot)

        msg = {'from': Jid('room', 'room@example.com', 'Rob')}
        match = re.search('!seen (?P<jid>.*)', '!seen lurker@example.com')
        result = self.cmd.report_jid(msg, match, self.bot)
        self.assertEqual(result,
            'Rob: lurker@example.com was last seen 100000000 seconds ago.')
