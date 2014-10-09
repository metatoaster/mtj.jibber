Introduction
============

mtj.jibber is a package that can be used to streamline the process of
providing automagical useless bantering onto your friendly neighbourhood
rooms (multi-user chat or MUCS) on all the Jabber (XMPP) servers.

It's jibber jabber time.

.. image:: https://travis-ci.org/metatoaster/mtj.jibber.png?branch=master
   :target: https://travis-ci.org/metatoaster/mtj.jibber
.. image:: https://coveralls.io/repos/metatoaster/mtj.jibber/badge.png?branch=master
   :target: https://coveralls.io/r/metatoaster/mtj.jibber?branch=master

Installation
============

This is a piece of cake.  Get a virtualenv running, and do this:

.. code:: sh

    $ pip install mtj.jibber

This installs the latest stable release version of this package from
the Python Package Index (pypi).  If you wish to do so, you should
follow the `documentation on that index page`_.

.. _documentation on that index page: https://pypi.python.org/pypi/mtj.jibber

Alternatively, if you want to hack and develop on this, please feel free
to make a fork and clone that or clone directly from this fork.
Naturally I will assume you got a virtualenv setup, too:

.. code:: sh

    $ git clone https://github.com/metatoaster/mtj.jibber.git
    $ cd mtj.jibber
    $ python setup.py develop

Of course, in that case you should follow the documentation as listed
in the README.rst found at the root of the source repository.

Quick Start Tutorial
====================

The original reason for making this is to allow much modularity and very
easy usage.  To demonstrate this, get this package installed and get the
default configuration files generated like so:

.. code:: sh

    $ jibber --gen-config server > server.config.json
    $ jibber --gen-config client > client.config.json

Now you can start the bot like so:

.. code:: sh

    $ jibber server.config.json client.config.json debug
    Starting interactive shell. `bot` is bound to the MucBot object.
    Try calling bot.connect() to connect to the server specified in config file.
    Note: process will NOT terminate if bot.is_alive() is False!
    Alternatively call bot_test() to test here locally.
    >>>

So the interactive shell should have started like it did above if this
package was installed correctly.  Now you can issue the command:

.. code:: python

    >>> bot_test()
    Test client ready; call client('Hello bot') to interact.
    >>>

A new function is provided for you to interact with the bot, you can
just follow the prompt:

.. code:: python

    >>> client('Hello bot')
    2013-11-01 00:00:51,316 INFO mtj.jibber.testing hi Tester
    >>>

The test client doesn't have any connection to any servers, so all the
interactions will just end up being shown in the log at the INFO level.
This can be useful for your final integration testing.

Of course, you want the bot to do more than this, let's look at the
client config file.

Client Config
-------------

The packages object contain the list of "packages" that will be
instantiated for the bot to use.  The keys follow:

package
    The full path to the class (or any callables that return an
    instance of one).
kwargs
    The keyword arguments that will be passed into that call.
commands
    A 2-tuple (well, list, this is JSON after all) of regex string,
    method.  The method is a callable attribute will be provided by
    the object returned by the calling ``package(**kwargs)``.  The
    regex can contain some string format keywords, most notably
    ``nickname`` which is the nickname assigned to the bot.
    Commands only get executed to the maximum commands limit, and
    the bot will not try to match something it says with the ones
    here.
commentators
    Exactly like commands, except the bot will try to comment on
    things it says up to a limit.  Default is sane, I am not going
    to teach you how to override that because hilarious infinite
    loops can happen
listeners
    All messages passed to the bot will be listened, but no output
    will be sent.
timers
    A list of objects that will be used to instantiate repeated
    commands at a delay.  This is somewhat advanced and not
    covered here.  The test cases might explain how this works.

The commands_max_match can be defined to match up to that amount of
commands, i.e. the commands will not further cascade down once that
amount is reached.  This is useful if you have a situation where a
significant amount of triggers overlap.

Now, you might want to extend the bot to do more.  Let's try something
adding something else to the list of packages (remember your JSON comma
placements!):

.. code:: json

    {
        "package": "mtj.jibber.bot.PickOne",
        "kwargs": {"items": [
            "red!", "orange!", "yellow!", "green!", "blue!", "violet!"]},
        "commands": [
            ["^rainbow (color|colour)!$", "play"]
        ]
    }

The PickOne class has a play method that picks one of the items with an
equal chance for all.  In this case a command that matches either
`rainbow color!` or `rainbow colour!` and respond with one of the six
items specified.  Demo run:

.. code:: python

    >>> client('rainbow color!')
    2013-11-01 00:01:31,965 INFO mtj.jibber.testing violet!
    >>> client('rainbow colour!')
    2013-11-01 00:01:33,981 INFO mtj.jibber.testing orange!

There is another one that is similar:

.. code:: json

    {
        "package": "mtj.jibber.bot.ChanceGame",
        "kwargs": {"chance_table": [
            [0.125, "%(mucnick)s: BOOM"], [1, "%(mucnick)s: click"]
        ]},
        "commands": [
            ["^%(nickname)s: rr$", "play"]
        ]
    }

This one is similar to PickOne, except with the allowance of a chance
which is specified in the first element of the 2-tuple.  The roll is a
random real number between 0 and 1 inclusive, and thus the matching is
done by cascading downwards on that list for a match.  Match is done by
checking whether the number is less than the chance number.  If match,
the corresponding result is returned.  Demo run:

.. code:: python

    >>> client('bot: rr')
    2013-11-01 00:02:11,647 INFO mtj.jibber.testing Tester: click
    >>> client('bot: rr')
    2013-11-01 00:02:12,714 INFO mtj.jibber.testing Tester: click
    >>> client('bot: rr')
    2013-11-01 00:02:12,822 INFO mtj.jibber.testing Tester: click
    >>> client('bot: rr')
    2013-11-01 00:02:13,006 INFO mtj.jibber.testing Tester: BOOM

Also note how it is possible to specify string format keywords here.
The most useful one would be mucnick, which correspond to the user
who sent the line.  These are based on the msg stanzas used by sleekxmpp
so for all details check the relevant documentation (or clever
breakpoint placements).

For completeness, if you had followed the above instructions your
configuration should look similar to the output generated by this
command:

.. code:: sh

    $ jibber --gen-config client_example

Oh yeah, you can naturally develop your own modules that do things you
want your bot to do.  Feel free to use the classes in mtj.jibber.bot as
your starting point!

Server Config
-------------

The server configuration should be simple.  It is done this way to split
out the connection settings from the actual bot settings you may wish to
pass onto your friends.  The keys as follows:

jid
    The jid that is used to connect to the server.
password
    Password associated with the jid
host
    The host used to connect to the server.  Optional as this can
    be derived from jid, but quite often the actual host is often
    different so this usually needs to be specified.
port
    Defaults to 5222.

Remaining keys are passed into the connect method for a sleekxmpp client
instance.  Refer to documentations over there if you are curious on what
they are.

Doing it live
-------------

Fill out the correct information (the jid/password/host and the rooms
you wish your bot to join) and then you can call ``bot.connect()``!
Alternatively you can replace ``debug`` with ``fg`` to have it connect
right away and ditch the interactive shell.

Bonus
-----

If you find yourself constantly restarting the bot completely because a
single line of code or setting was changed and also finding this process
tiresome, there is a helper method in the debug shell that will reload
the client configuration file and all modules with the associated timers
and triggers with just one function call:

.. code:: python

    >>> bot_reinit()
    Successfully reinitialized bot configuration and modules.
    >>>

Do note: this function is potentially unsafe.  Syntax errors in the
configuration or the modules that got added after the bot has started
will be raised as exceptions and loading is aborted, leaving the bot
in a fresh but partially instantiated state.  This may or may not cause
problems specific to the code/modules you have loaded with the bot.
