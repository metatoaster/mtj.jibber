import re
import random
from time import time

from mtj.jibber.core import Command
from mtj.jibber import stanza


class FakeActions(Command):

    punctuation = re.compile('[\.\?\!\,]*$')

    def do_things(self, msg, match, **kw):
        """
        Expects a regex with groups matched.  Example regex might be
        like this inside the configuration file.

            ^%(nickname)s: go (.*)

        >>> act = FakeActions()
        >>> regexp = re.compile('go (.*)')
        >>> match = regexp.search('go write better code')
        >>> act.do_things({'mucnick': 'Tester'}, match)
        'Tester: Okay, I will write better code.'
        """

        action = self.punctuation.sub('', match.groups()[0])
        return '%s: Okay, I will %s.' % (msg['mucnick'], action)


class Fortune(Command):
    """
    Give a random fortune.

    fortune_items
        Alternatively, specify a list of strings to be used as fortunes.

    >>> fortune = Fortune()
    Traceback (most recent call last):
    ...
    TypeError: ...
    >>> fortune = Fortune(fortune_items=['Stick with what you got.'])
    >>> fortune.fortune({'mucnick': 'Tester'}, None)
    'Tester: Stick with what you got.'

    HTML will be rendered.

    >>> fortune = Fortune(fortune_items=['<strong>So very strong</strong>.'])
    >>> fortune.fortune({'mucnick': 'Tester'}, None)
    '<html><body>Tester: <strong>So very strong</strong>.</body></html>'
    """

    def __init__(self, fortune_items=None):
        if not isinstance(fortune_items, list):
            raise TypeError('please specify a list of fortune_items')
        self._fortune = lambda: random.choice(fortune_items)

    def fortune(self, msg, match, **kw):
        fortune = self._fortune().strip()
        if not fortune.startswith('<'):
            return '%s: %s' % (msg['mucnick'], fortune)
        return '<html><body>%s: %s</body></html>' % (msg['mucnick'], fortune)


class ChanceGame(Command):
    """
    A game of chance.

    Accepts a list of 2-tuple in the format of chance and response.

    Chance should be ordered in incremental real numbers < 1.
    Response is the message associated with the chance to trigger.

    >>> cg = ChanceGame((
    ...     (0.1, 'You are dead.'),
    ...     (1, 'You live!'),
    ... ))
    >>> cg.play({'mucnick': 'Tester'}, None)
    'You...'

    The parameter can alternatively be a callable, too.

    >>> def dummy(msg, match, **kw):
    ...     return 'No way, %(mucnick)s.'
    >>> cg = ChanceGame(((1, dummy),))
    >>> cg.play({'mucnick': 'Tester'}, None)
    'No way, Tester.'

    Alternatively, insufficient chances will result in no output.

    >>> cg = ChanceGame(((-0.1, 'This has no chance'),))
    >>> cg.play({'mucnick': 'Tester'}, None)
    ''
    """

    def __init__(self, chance_table):
        self.chance_table = chance_table

    def play(self, msg, match, **kw):
        chance = random.random()
        for trigger, response in self.chance_table:
            if chance <= trigger:
                if callable(response):
                    response = response(msg, match, **kw)
                return response % msg
        return ''


class PickOne(Command):
    """
    Pick a response.

    Accepts a list of strings or callables that will generate a
    response.

    >>> po = PickOne(('%(mucnick)s: red', '%(mucnick)s: green',
    ...     '%(mucnick)s: blue'))
    >>> po.play({'mucnick': 'Tester'}, None)
    'Tester: ...'

    The parameter can alternatively be a callable, too.

    >>> def dummy(msg, match, **kw):
    ...     return 'No way, %(mucnick)s.'
    >>> po = PickOne((dummy,))
    >>> po.play({'mucnick': 'Tester'}, None)
    'No way, Tester.'
    """

    def __init__(self, items):
        self.items = items

    def play(self, msg, match, **kw):
        result = random.choice(self.items)
        if callable(result):
            return result(msg, match, **kw) % msg
        return result % msg


class PercentageChance(Command):
    """
    Generates a float between 0-100.

    Accepts a format string to determine response, for example:

        >>> pc = PercentageChance(
        ...     '%(mucnick)s: We have a %(chance).2f%% chance of survival.')
        >>> pc.play({'mucnick': 'Tester'}, None)
        'Tester: We have a ... chance of survival.'

    Of course, if you want him to match some strings provided by the
    matched input, you can try to install with a regex that contain a
    named capturing group.

        >>> regexp = re.compile('How likely will it (?P<thing>[\\w\\s]*)')
        >>> match = regexp.search('How likely will it rain tomorrow?')
        >>> pc = PercentageChance(
        ...     '%(mucnick)s: There is a %(chance).2f%% chance it will '
        ...     '%(thing)s.')
        >>> pc.play({'mucnick': 'Tester'}, match)
        'Tester: There is a ... chance it will rain tomorrow.'
    """

    def __init__(self, template):
        self.template = template

    def play(self, msg, match, **kw):
        items = {'chance': random.random() * 100}
        items.update(msg)
        if match:
            items.update(match.groupdict())
        return self.template % items


class MucAdmin(Command):
    """
    Provides some basic administration capabilities for a MUC.

    Currently experimental as it pokes into methods exposed by the bot.
    """

    def __init__(self,
            success_reason='Requested by moderator',
            success_msg='%(mucnick)s: Okay, I have kicked %(victim)s for you.',
            forbidden_reason='Only moderators may kick',
            allowed_roles=('moderator',),
        ):
        self.success_reason = success_reason
        self.success_msg = success_msg
        self.forbidden_reason = forbidden_reason
        self.allowed_roles = allowed_roles

    def admin_kick_nickname(self, msg, match, bot, **kw):
        """
        Allow those who have the role in allowed_roles do the kicking,
        and kick those who are not.
        """

        room = msg['from'].bare
        req_nick = msg['from'].resource

        self_role = bot.muc.rooms.get(room, {}).get(bot.nickname,
            {}).get('role')
        if self_role != 'moderator':
            return

        roster = bot.muc.rooms.get(room, {})
        roster_item = roster.get(req_nick)

        if not roster_item:
            # warning?
            return

        if roster_item['role'] not in self.allowed_roles:
            raw = stanza.admin_query(room, nick=req_nick,
                reason=self.forbidden_reason)
            bot.client.send(raw)
            return

        victim = match.groupdict().get('victim')
        if not victim or not roster.get(victim):
            return

        raw = stanza.admin_query(room, nick=victim, reason=self.success_reason)
        bot.client.send(raw)
        return self.success_msg % {
            'mucnick': msg['mucnick'],
            'victim': victim,
        }


class RussianRoulette(Command):
    """
    Only way to win is not to play.
    """

    def __init__(self,
            bullets=5,
            slots=6,
            empty_msg='*click*... it appears %(mucnick)s lives another day.',
            death_msg='*splat*',
        ):
        self.bullets = bullets
        self.slots = slots
        self.empty_msg = empty_msg
        self.death_msg = death_msg

    def play(self, msg, match, bot, **kw):
        spin = random.randint(1, self.slots)
        if spin > self.bullets:
            return self.empty_msg % msg

        room = msg['from'].bare
        nick = msg['mucnick']

        raw = stanza.admin_query(room, nick=nick, reason=self.death_msg)
        bot.client.send(raw)


class LastActivity(Command):
    """
    This is a base implementation, a more detailed one that includes
    persistency will be included in mtj.jibberext.

    Can effectively provide the the last seen command typically found in
    IRC chatrooms when associated with the right triggers.
    """

    def __init__(self):
        self.jids = {}
        self.nicks = {}

    def add_jid(self, room_jid, jid, nick, timestamp):
        self.jids[(room_jid, jid)] = (nick, timestamp)

    def add_nick(self, room_jid, jid, nick, timestamp):
        self.nicks[(room_jid, nick)] = (jid, timestamp)

    def add_all(self, room_jid, jid, nick, timestamp):
        self.add_jid(room_jid, jid, nick, timestamp)
        self.add_nick(room_jid, jid, nick, timestamp)

    def add_roster(self, msg, match, bot, **kw):
        """
        Base activity on roster.  Usage is good for bot's first log-in,
        or timer based checks.
        """

        timestamp = int(time())
        for room, users in bot.muc.rooms.items():
            for user in users.values():
                self.add_all(room, user['jid'].bare, user['nick'], timestamp)
