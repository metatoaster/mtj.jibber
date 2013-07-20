import re

def strip_tags(html):
    if html is None:
        return None
    
    return re.compile('<[^>]*>').sub('', html)
