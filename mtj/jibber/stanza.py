# from xml.etree import cElementTree as ET
from sleekxmpp.xmlstream import ET
from sleekxmpp.stanza import Iq

def admin_query(room, nick=None, jid=None, role='none', reason=None):
    """
    Generate an admin query stanza that will change the role of the
    nick or the full jid within a muc.

    Default role is 'none', which kicks the nick/jid from the muc.

    If only sleekxmpp provide a better support for this in their
    xep_0045 plugin...
    """

    roles = ('moderator', 'none', 'participant', 'visitor')
    if role not in roles:
        raise TypeError('role must be one of %s' % str(roles))

    query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
    if nick is not None:
        item = ET.Element('{http://jabber.org/protocol/muc#admin}item',
            {'role': role, 'nick': nick})
    elif jid is not None:
        item = ET.Element('{http://jabber.org/protocol/muc#admin}item',
            {'role': role, 'jid': jid})
    else:
        raise ValueError('either nick or jid must be provided')

    if reason:
        el = ET.Element('reason')
        el.text = reason
        item.append(el)

    query.append(item)

    iq = Iq()
    iq.append(query)
    iq['to'] = room
    iq['type'] = 'set'

    return iq
