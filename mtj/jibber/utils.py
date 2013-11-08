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
