import logging
from functools import partial

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
        Auto rejoin immediately when kicked from a muc.
        """

        if msg['to'] != bot.jid:
            # Do nothing, not this bot.
            return

        # no waiting.
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
            logger.info('Rejoining %s', target)
            bot.muc.joinMUC(target, bot.nickname)