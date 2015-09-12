import logging
from functools import partial
import re

from mtj.jibber.core import Presence

logger = logging.getLogger(__name__)


class Muc(Presence):
    """
    Commom presence handlers for multi-user chats.
    """

    def __init__(self,
            auto_rejoin_timeout=0,
        ):

        self.auto_rejoin_timeout = auto_rejoin_timeout

    def auto_rejoin(self, msg, bot=None, **kw):
        """
        Auto rejoin immediately when kicked from a muc.  Typical use
        case:

        {
            "package": "mtj.jibber.presence.Muc",
            "alias": "muc",
            "kwargs": {
                "auto_rejoin_timeout": 3
            },
            "raw_handlers": {
                "presence_unavailable": [
                    "auto_rejoin"
                ]
            }
        }

        Omit the ``auto_rejoin_timeout`` kwargs if immediate rejoin is
        desired.
        """

        if msg['to'] != bot.jid or msg['from'].resource != bot.nickname:
            # Do nothing, not this bot.
            return

        target = msg['from'].bare

        if self.auto_rejoin_timeout:
            # using the underlying client class directly as the user
            # likely wants the bot to reconnect even if this object may
            # be resetted due to external causes, and also there are no
            # methods called that are sensitive to reinitialization.
            wait = self.auto_rejoin_timeout
            try:
                bot.client.schedule('Rejoin %s' % target,
                    wait, partial(bot.muc.joinMUC, target, bot.nickname),
                )
                logger.info('Rejoining %s in %d seconds', target, wait)
            except ValueError:
                logger.warning('Rejoining of %s already scheduled', target)
        else:
            # no waiting.
            logger.info('Rejoining %s', target)
            bot.muc.joinMUC(target, bot.nickname)


class MucGreeter(Presence):
    """
    A basic greeter, most basic case:

    {
        "package": "mtj.jibber.presence.MucGreeter",
        "alias": "mucgreeter",
        "kwargs": {},
        "raw_handlers": {
            "presence_available": [
                "greeter"
            ]
        }
    }
    """


    def __init__(self,
            greet_muc=None,
            greet_nick=None,
            greet_msg='Hello %(nick)s',
            greet_role='participant',
        ):

        # In the form mucroom@example.com/resource
        self.greet_muc = greet_muc and re.compile(greet_muc)
        self.greet_nick = greet_nick and re.compile(greet_nick)
        self.greet_msg = greet_msg
        self.greet_role = greet_role

    def greeter(self, msg, bot=None):
        nick = msg['from'].resource
        room = msg['from'].bare

        # Given patterns for the next two fields, no match, no greet
        if self.greet_muc and not self.greet_muc.search(room):
            return
        if self.greet_nick and not self.greet_nick.search(nick):
            return

        # Only greet one specific role.
        if not msg.get('muc').get('role') == self.greet_role:
            return

        raw = self.greet_msg % {'nick': nick}
        bot.send_message(room, raw=raw, mtype='groupchat')
