TrueSkill
=========

The video game rating system

.. currentmodule:: trueskill

What is TrueSkill?
~~~~~~~~~~~~~~~~~

TrueSkill_ is a skill-based ranking system that can be used across a wide variety
of games. It was developed by `Microsoft Research`_ and has been used on `Xbox LIVE`_ 
for ranking and matchmaking services.  This system quantifies players' **TRUE** skill
level by using the Bayesian inference algorithm.  It also works well with any type of match
rule including N:N team games or free-for-all.

This project is a Python package which implements the TrueSkill rating
system::

   from trueskill import Rating, quality_1vs1, rate_1vs1
   alice, bob = Rating(25), Rating(30)  # assign Alice and Bob's ratings
   if quality_1vs1(alice, bob) < 0.50:
       print('This match seems to be not so fair')
   alice, bob = rate_1vs1(alice, bob)  # update the ratings after the match

.. _TrueSkill: http://research.microsoft.com/en-us/projects/trueskill
.. _Microsoft Research: http://research.microsoft.com/
.. _Research: http://research.microsoft.com/
.. _Xbox LIVE: http://www.xbox.com/live

Installing
~~~~~~~~~~

The package is available in `PyPI <http://pypi.python.org/pypi/trueskill>`_:

.. sourcecode:: bash

   $ pip install trueskill

Learning
~~~~~~~~

Rating, the model for skill
---------------------------

In TrueSkill, the rating is represented by a Gaussian distribution which starts from
:math:`\mathcal{ N }( 25, \frac{ 25 }{ 3 }^2 )`.  :math:`\mu` is the average
skill of a player, and :math:`\sigma` is the confidence of the estimated rating.  The
actual skill of a player falls within the range :math:`\mu \pm 2\sigma` with 95% confidence.

::

   >>> from trueskill import Rating
   >>> Rating()  # use the default mu and sigma
   trueskill.Rating(mu=25.000, sigma=8.333)

If a player's rating is :math:`\beta` higher than another player's rating, the
first player would have a 76% (specifically :math:`\Phi(\frac {1}{\sqrt{2}})`)
chance of beating the second player in a match.  The default value of :math:`\beta` is
:math:`\frac{ 25 }{ 6 }`.

Ratings gradually converge towards the actual skill level of a player after a 
certain number of matches, thanks to TrueSkill's Bayesian inference algorithm.
How many? It depends on the game mode.  See the table below:

================  =======
Game Mode         Matches
================  =======
16P free-for-all  3
8P free-for-all   3
4P free-for-all   5
2P free-for-all   12
2:2:2:2           10
4:4:4:4           20
4:4               46
8:8               91
================  =======

Head-to-head (1 vs. 1) game mode
---------------------------------

Most games follow a 1:1 game mode.  If yours does as well, just use the
``_1vs1`` shortcuts containing :func:`rate_1vs1` and :func:`quality_1vs1`.
These are very easy to use.

First of all, we need 2 :class:`Rating` objects::

   >>> r1 = Rating()  # P1's skill
   >>> r2 = Rating()  # P2's skill

Then we can guess the quality of the match, which is also equivalent to the probability of a draw,
by using :func:`quality_1vs1`::

   >>> print('{:.1%} chance to draw'.format(quality_1vs1(r1, r2)))
   44.7% chance to draw

After the game, TrueSkill recalculates their ratings according to the result.
For example, if Player 1 beats Player 2::

   >>> new_r1, new_r2 = rate_1vs1(r1, r2)
   >>> print(new_r1)
   trueskill.Rating(mu=29.396, sigma=7.171)
   >>> print(new_r2)
   trueskill.Rating(mu=20.604, sigma=7.171)

The mu value is related to the player's performance.  A higher value signifies a higher
skill level.  Meanwhile, the value of sigma is tied to the number of games, and reflects
the algorithm's confidence in the player's skill assessment.  A lower number indicates more confidence.

So for P1, the skill increased from 25 to 29.396. While for P2, who lost the game, the skill level shrank
to 20.604.  The sigma value also decreased by the same amount for both players.

Of course, you can also handle a tie by using ``drawn=True``::

   >>> new_r1, new_r2 = rate_1vs1(r1, r2, drawn=True)
   >>> print(new_r1)
   trueskill.Rating(mu=25.000, sigma=6.458)
   >>> print(new_r2)
   trueskill.Rating(mu=25.000, sigma=6.458)

Other game modes
-----------------

Additional game modes include N:N team matches, N:N:N multiple team matches,
N:M unbalanced matches, free-for-all (Player vs. All), and various others.
Most rating systems aren't able to handle these game modes, but TrueSkill can.
In fact, TrueSkill works with any game mode.

To represent team-based game modes, we need to create a list for each team.
Within these lists, we'll place the rating of each player of the team::

   >>> r1 = Rating()  # P1's skill
   >>> r2 = Rating()  # P2's skill
   >>> r3 = Rating()  # P3's skill
   >>> t1 = [r1]  # Team A only has P1
   >>> t2 = [r2, r3]  # Team B has P2 and P3

Then we can calculate the match quality and rate them::

   >>> print('{:.1%} chance to draw'.format(quality([t1, t2])))
   13.5% chance to draw
   >>> (new_r1,), (new_r2, new_r3) = rate([t1, t2], ranks=[0, 1])
   >>> print(new_r1)
   trueskill.Rating(mu=33.731, sigma=7.317)
   >>> print(new_r2)
   trueskill.Rating(mu=16.269, sigma=7.317)
   >>> print(new_r3)
   trueskill.Rating(mu=16.269, sigma=7.317)

If you want to describe other game results, set the ``ranks`` argument as shown below:

- A drawn game -- ``ranks=[0, 0]``
- Team B won not team A -- ``ranks=[1, 0]`` (Lower rank is better)

Here are other examples for different game modes.  All variables which
start with ``r`` are :class:`Rating` objects:

- N:N team match -- ``[(r1, r2, r3), (r4, r5, r6)]``
- N:N:N multiple team match -- ``[(r1, r2), (r3, r4), (r5, r6)]``
- N:M unbalanced match -- ``[(r1,), (r2, r3, r4)]``
- Free-for-all -- ``[(r1,), (r2,), (r3,), (r4,)]``

Partial play
------------

Let's assume that there are 2 teams, with 2 players each.  The game was 1 hour long,
but one of the players on the first team entered the game 30 minutes after the
start of the match.

If some player wasn't present for the entire duration of the game, we can use the
concept of "partial play" by using the ``weights`` parameter.
This situation can be described by the following weights:

.. hlist::
   - P1 on team A -- 1.0 = Full time
   - P2 on team A -- 0.5 = :math:`\frac{ 30 }{ 60 }` minutes
   - P3 on team B -- 1.0
   - P4 on team B -- 1.0

In code, using a 2-dimensional list::

   # set each weights to 1, 0.5, 1, 1.
   rate([(r1, r2), (r3, r4)], weights=[(1, 0.5), (1, 1)])
   quality([(r1, r2), (r3, r4)], weights=[(1, 0.5), (1, 1)])

Or with a dictionary.  Each key is a tuple of
``(team_index, index_or_key_of_rating)``::

   # set a weight of 2nd player in 1st team to 0.5, otherwise leave as 1.
   rate([(r1, r2), (r3, r4)], weights={(0, 1): 0.5})
   # set a weight of Carol in 2nd team to 0.5, otherwise leave as 1.
   rate([{'alice': r1, 'bob': r2}, {'carol': r3}], weights={(1, 'carol'): 0.5})

Backends
--------

The TrueSkill algorithm uses :math:`\Phi`, `the cumulative distribution
function`_; :math:`\phi`, `the probability density function`_; and
:math:`\Phi^{-1}`, the inverse cumulative distribution function.  But the standard
mathematics library doesn't provide these functions.  Therefore this package
implements them.

There are also third-party libraries which implement these functions.
If prefer to use another one, you can set the ``backend`` option of :class:`TrueSkill`
to the backend of your choice:

>>> TrueSkill().cdf  # internal implementation
<function cdf at ...>
>>> TrueSkill(backend='mpmath').cdf  # mpmath.ncdf
<bound method MPContext.f_wrapped of <mpmath.ctx_mp.MPContext object at ...>>

Here's the list of available backends:

- ``None`` -- the internal implementation.  (Default)
- "mpmath" -- requires mpmath_ installed.
- "scipy" -- requires scipy_ installed.

.. note::

   When winners have a much lower rating than losers, :meth:`TrueSkill.rate` will
   raise :exc:`FloatingPointError`.  In this case, you will need higher
   floating-point precision.  The mpmath library offers flexible floating-point
   precision.  You can solve the problem with mpmath as a backend and higher
   precision setting.

.. _the cumulative distribution function:
   http://en.wikipedia.org/wiki/Cumulative_distribution_function
.. _the probability density function:
   http://en.wikipedia.org/wiki/Probability_density_function
.. _mpmath: https://code.google.com/p/mpmath
.. _scipy: http://www.scipy.org/

Win probability
---------------

TrueSkill provides the (:func:`quality`) function to calculate the probability of a
draw between arbitrary ratings. Unfortunately, there is no function for win probability. 

If you need to calculate the win probability between 2 teams, you
can use this code snippet::

   import itertools
   import math

   import trueskill

   def win_probability(team1, team2, draw_margin=0, env=None):
       if env is None:
           env = trueskill.global_env()
       beta = env.beta
       delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
       sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
       size = len(team1) + len(team2)
       denom = math.sqrt(size * (beta * beta) + sum_sigma)
       return env.cdf((delta_mu - draw_margin) / denom)

This snippet was written by `Juho Snellman`_ and `@coldfix`_ in `issue #1`_.

.. _Juho Snellman:
   https://www.snellman.net/
.. _@coldfix: https://github.com/coldfix
.. _issue #1:
   https://github.com/sublee/trueskill/issues/1#issuecomment-149762508

API
~~~

TrueSkill objects
-----------------

.. autoclass:: Rating
   :members: mu,
             sigma,

.. autoclass:: TrueSkill
   :members: create_rating,
             rate,
             quality,
             expose,
             make_as_global,

Default values
--------------

.. autodata:: MU
.. autodata:: SIGMA
.. autodata:: BETA
.. autodata:: TAU
.. autodata:: DRAW_PROBABILITY

Head-to-head shortcuts
----------------------

.. autofunction:: rate_1vs1
.. autofunction:: quality_1vs1

Functions for the global environment
------------------------------------

.. autofunction:: global_env
.. autofunction:: setup
.. autofunction:: rate
.. autofunction:: quality
.. autofunction:: expose

Draw probability helpers
------------------------

.. autofunction:: calc_draw_probability
.. autofunction:: calc_draw_margin

Mathematical statistics backends
--------------------------------

.. module:: trueskill.backends

.. autofunction:: trueskill.backends.choose_backend
.. autofunction:: trueskill.backends.available_backends

Changelog
~~~~~~~~~

.. include:: ../changelog.rst

More about TrueSkill
~~~~~~~~~~~~

A mailing list is available for the users of this package.  To subscribe, just send an email to
trueskill@librelist.com.

If you'd like to delve deeper into how the TrueSkill algorithm works, also see:

- `TrueSkill: A Bayesian Skill Rating System
  <http://research.microsoft.com/apps/pubs/default.aspx?id=67956>`_
  by Herbrich, Ralf and Graepel, Thore
- `TrueSkill Calculator
  <http://atom.research.microsoft.com/trueskill/rankcalculator.aspx>`_
  by Microsoft Research
- `Computing Your Skill <http://bit.ly/computing-your-skill>`_ by Jeff Moser
- `The Math Behind TrueSkill <http://bit.ly/the-math-behind-trueskill>`_ by
  Jeff Moser
- `Application and Further Development of TrueSkill™ Ranking in Sports
  <http://uu.diva-portal.org/smash/get/diva2:1322103/FULLTEXT01.pdf>` (2019)
  by Ibstedt, Rådahl, Turesson, vande Voorde

Licensing and Author
~~~~~~~~~~~~~~~~~~~~

This TrueSkill package is opened under the BSD_ license but the `TrueSkill™`_
brand is not.  Microsoft permits only Xbox Live games or non-commercial projects
to use TrueSkill™.  If your project is commercial, you should find another
rating system.  See LICENSE_ for the details.

I'm `Heungsub Lee`_, a game developer.  Any regarding questions or patches are
welcomed.

.. _BSD: http://en.wikipedia.org/wiki/BSD_licenses
.. _TrueSkill™: http://research.microsoft.com/en-us/projects/trueskill
.. _LICENSE: https://github.com/sublee/trueskill/blob/master/LICENSE
.. _Heungsub Lee: http://subl.ee/
