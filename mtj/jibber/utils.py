import re

def strip_tags(html):
    """
    Lazily strip all tags in a very lazy way.

    >>> print(strip_tags(None))
    None
    >>> print(strip_tags('test string'))
    test string
    >>> print(strip_tags('test <b>string</b>'))
    test string
    >>> print(strip_tags('<test string>'))
    <BLANKLINE>
    """

    if html is None:
        return None
    
    return re.compile('<[^>]*>').sub('', html)

def read_config(config_path):
    try:
        with open(config_path) as fd:
            return fd.read()
    except IOError:
        return None


class ConfigFile(object):

    def __init__(self, path, consumer):
        self.path = path
        self.consumer = consumer

    def load(self):
        config = read_config(self.path)
        if config is None:
            return
        self.consumer(config)
        return config
