TrueSkill
=========

Bayesian skill rating system

.. currentmodule:: trueskill

What's TrueSkiil?
~~~~~~~~~~~~~~~~~

`TrueSkill`_ is a rating system among game players. It has been used on `Xbox
Live`_ to rank and match players. TrueSkill system quantizes **TRUE** skill
points by a Bayesian inference algorithm.

With TrueSkill, you can measure players' skill; make the best matches by skill
points; predict who's going to win. And even it works with N:N:N, a multiple
team game even a free-for-all not only 1:1 game.

This project is a Python package which implements TrueSkill rating system.

.. _TrueSkill: http://research.microsoft.com/en-us/projects/trueskill
.. _Xbox Live: http://www.xbox.com/live

Learning
~~~~~~~~

Rating, a model for player's skill
----------------------------------

In TrueSkill, rating is a Gaussian distribution. The initial mu (\\(\\mu\\);
mean) of rating is 25 and the initial sigma (\\(\\sigma\\); standard deviation)
is \\(\\frac{ 25 }{ 3 } \\approx 8.333\\):

::

   >>> from trueskill import Rating
   >>> my_player.rating = Rating()
   >>> print my_player.rating
   trueskill.Rating(mu=25.000, sigma=8.333)

1:1 competition game
--------------------

Most competition games follows 1:1 match rule. If your game does, just use
``1vs1`` helpers containing :func:`rate_1vs1` and :func:`quality_1vs1`. These
are very easy to use.

First of all, we need 2 :class:`Rating` objects:

::

    >>> r1 = Rating()  # 1P's skill
    >>> r2 = Rating()  # 2P's skill

Then we can guess match quality which is equivalent with draw probability of
this match using :func:`quality_1vs1`:

::

    >>> print '{:.1%} chance to draw'.format(quality_1vs1(r1, r2))
    44.7% chance to draw

After the game, TrueSkill recalculates their ratings by the game result. For
example, if 1P beats 2P:

::

    >>> new_r1, new_r2 = rate_1vs1(r1, r2)
    >>> print new_r1
    trueskill.Rating(mu=29.396, sigma=7.171)
    >>> print new_e2
    trueskill.Rating(mu=20.604, sigma=7.171)

Mu value follows player's win/draw/lose records. Higher value means higher game
skill. And sigma value follows the number of games. Lower value means many game
plays and higher rating confidence.

So 1P, a winner's skill grew up from 25 to 29.396 but 2P, a loser's skill shrank
to 20.604. And both sigma values became narrow about same magnitude.

Matchmaking
-----------

Draw probability is match quality. If you're making a matchmaking service,
match quality will be helpful:

::

    while should_match:
        r1, r2 = next_match()
        if quality_1vs1(r1, r2) < .30:
            rematch(r1, r2)
            continue
        succeed_match(r1, r2)
        time.sleep(match_interval)

API
~~~

TrueSkill objects
-----------------

.. autoclass:: TrueSkill
   :members: create_rating,
             rate,
             quality,
             rate_1vs1,
             quality_1vs1,
             make_as_global,

.. autoclass:: Rating
   :members: exposure

Proxy functions of the global environment
-----------------------------------------

.. autofunction:: rate

.. autofunction:: quality

.. autofunction:: rate_1vs1

.. autofunction:: quality_1vs1

.. autofunction:: setup

Constants
---------

.. autodata:: MU

.. autodata:: SIGMA

.. autodata:: BETA

.. autodata:: TAU

.. autodata:: DRAW_PROBABILITY

Installing
~~~~~~~~~~

The package is available in `PyPI <http://pypi.python.org/pypi/trueskill>`_. To
install it in your system, use `easy_install`:

.. sourcecode:: bash

   $ easy_install trueskill

Or check out developement version:

.. sourcecode:: bash

   $ git clone git://github.com/sublee/trueskill.git

Changelog
~~~~~~~~~

.. include:: ../CHANGES

Further Reading
~~~~~~~~~~~~~~~

If you want to more details of the TrueSkill algorithm, see also:

- `TrueSkill™ Ranking System
  <http://research.microsoft.com/en-us/projects/trueskill/>`_ by Microsoft
- `Computing Your Skill <http://bit.ly/moserware-trueskill>`_ by Jeff Moser
- `The Math Behind TrueSkill <http://bit.ly/trueskill-math>`_ by Jeff Moser
- `TrueSkill Calcurator
  <http://atom.research.microsoft.com/trueskill/rankcalculator.aspx>`_
  by Microsoft

Licensing and Author
~~~~~~~~~~~~~~~~~~~~

This project is licensed under BSD_. See LICENSE_ for the details.

I'm `Heungsub Lee`_, a game developer. Any regarding questions or patches are
welcomed.

.. _BSD: http://en.wikipedia.org/wiki/BSD_licenses
.. _LICENSE: https://github.com/sublee/trueskill/blob/master/LICENSE
.. _Heungsub Lee: http://subl.ee/
