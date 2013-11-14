import re
import random

from mtj.jibber.core import Command


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
