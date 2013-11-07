import re
import random

from mtj.jibber.core import Command


class FakeActions(Command):

    punctuation = re.compile('[\.\?\!\,]*$')

    def do_things(self, msg, match):
        """
        Expects a regex with groups matched.  Example:

            ^%(nickname)s: go (.*)
        """

        action = self.punctuation.sub('', match.groups()[0])
        return '%s: Okay, I will %s.' % (msg['mucnick'], action)


class Fortune(Command):

    def __init__(self, fortune_file):
        import fortune

        fortune.make_fortune_data_file(fortune_file, quiet=True)
        self._fortune = lambda: fortune.get_random_fortune(fortune_file)

    def fortune(self, msg, match):
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

    >>> def dummy(msg, match):
    ...     return 'No way, %(mucnick)s.'
    >>> cg = ChanceGame((
    ...     (1, dummy),
    ... ))
    >>> cg.play({'mucnick': 'Tester'}, None)
    'No way, Tester.'
    """

    def __init__(self, chance_table):
        self.chance_table = chance_table

    def play(self, msg, match):
        chance = random.random()
        for trigger, response in self.chance_table:
            if chance <= trigger:
                if callable(response):
                    response = response(msg, match)
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

    >>> def dummy(msg, match):
    ...     return 'No way, %(mucnick)s.'
    >>> po = PickOne((dummy,))
    >>> po.play({'mucnick': 'Tester'}, None)
    'No way, Tester.'
    """

    def __init__(self, items):
        self.items = items

    def play(self, msg, match):
        result = random.choice(self.items)
        if callable(result):
            return result(msg, match) % msg
        return result % msg
