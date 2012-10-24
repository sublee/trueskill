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
team game not only 1:1 game.

This project is a Python package which implements TrueSkill rating system.

.. _TrueSkill: http://research.microsoft.com/en-us/projects/trueskill
.. _Xbox Live: http://www.xbox.com/live

Tutorial
~~~~~~~~

Measure player's skill
----------------------

Let's suppose that our sample game is 2v1. :class:`Rating` objects mean each
game players' skill points:

::

   >>> from trueskill import Rating
   >>> r1, r2, r3 = Rating(), Rating(), Rating()
   >>> team1 = (r1, r2)
   >>> team2 = (r3,)

TrueSkill system uses Gaussian distribution as player's skill point. The
initial mu (\\(\\mu\\); mean) of rating is 25 and the initial sigma
(\\(\\sigma\\); standard deviation) is \\(\\frac{ 25 }{ 3 } \\approx 8.333\\):

::

   >>> [team1, team2]
   [(
     Rating(mu=25.000, sigma=8.333),
     Rating(mu=25.000, sigma=8.333)
   ), (
     Rating(mu=25.000, sigma=8.333)
   )]

The first team has won the game. See the below transformation of the ratings:

::

   >>> import trueskill
   >>> truskill.rate([team1, team2])
   [(
     Rating(mu=25.604, sigma=8.075),
     Rating(mu=25.604, sigma=8.075)
   ), (
     Rating(mu=24.396, sigma=8.075)
   )]

The mu values in the first team transform from 25.000 to 25.604 and in the
second team transform from 25.000 to 24.396. The ratings were transformed just
a little. But, how does it work if the second team player has beaten 2 players
in the first team, by himself?

::

   >>> trueskill.rate([team1, team2], ranks=[1, 0]) # reversed ranks
   [(
     Rating(mu=16.269, sigma=7.317),
     Rating(mu=16.269, sigma=7.317)
   ), (
     Rating(mu=33.731, sigma=7.317)
   )]

In the first team, 25.000 to 16.269 and in the second team 25.000 to 33.731.
Now we have large transformations because it is a surprising result that 1
player beats 2 players.

It is just a simplest example. TrueSkill can estimate accurate skills in this
way. We only need enough game results!

Match quality
-------------

We also can calculate the fairness of any games with :func:`quality` function:

.. sourcecode:: python

   >>> import trueskill
   >>> trueskill.quality([team1, team2])
   0.1346981464530322

The result shows that the probability of a draw game is 13.47%. Let's see
another result of a really fair game:

.. sourcecode:: python

   >>> trueskill.quality([(Rating(25, 0.001),), (Rating(25, 0.001),)])
   0.9999999712000012

A much exact skill point follows very low sigma value such as the above ratings
(\\(\\sigma=0.001\\)). Very low sigma value indicates that the rating is much
more precise. Also, because of the same ratings, TrueSkill assures a draw of
this game, a super-fair game.

This feature would help you implement a fair match making system.

Make players happy
------------------

A skill point is a numeric representation of a player's ability. Someday, this
value will be convergent to the value that's exactly we are finding. But the
value can be a less than the initial value (\\(\\mu=25\\)). To prevent players
from despairing by knowing their own rating directly, we need to deceive our
players into growing up in general.

Okay, enough for the reason but how? Just use :attr:`Rating.exposure` property:

$$ E = \\mu - 3\\sigma $$

.. sourcecode:: python

   >>> Rating().exposure
   0.0
   >>> Rating(mu=24, sigma=7).exposure # mu -= 1
   2.9999999999999964
   >>> Rating(mu=22, sigma=6).exposure # mu -= 2
   4.0
   >>> Rating(mu=26, sigma=5).exposure # mu += 4
   11.0

An exposure value starts from 0 instead of 25. It can decrease sometimes but
the growth graph will go up on the whole.

API
~~~

TrueSkill objects
-----------------

.. autoclass:: TrueSkill
   :members: create_rating, rate, quality, make_as_global

.. autoclass:: Rating
   :members: exposure

Proxy functions of the global environment
-----------------------------------------

.. autofunction:: rate

.. autofunction:: quality

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
