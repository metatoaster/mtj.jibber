import re

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
