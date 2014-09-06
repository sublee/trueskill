Version 0.4.3
-------------

Released on Sep 4th 2014.

Fixes ordering bug on weights argument as a dict. This was reported at
`issue #9`_.

.. _issue #9: https://github.com/sublee/trueskill/issues/9

Version 0.4.2
-------------

Released on Jun 13th 2014.

Updates only meta code such as :file:`setup.py`.

Version 0.4.1
-------------

Released on Jun 6th 2013.

Deprecates :func:`dynamic_draw_probability`.

Version 0.4
-----------

Released on Mar 25th 2013.

- Supports dynamic draw probability.
- Replaces :meth:`Rating.exposure` with :meth:`TrueSkiil.expose`. Because the
  TrueSkill settings have to adjust a fomula to calculate an exposure.
- Deprecates head-to-head shortcut methods in :class:`TrueSkill`. The top-level
  shortcut functions are still alive.

Version 0.3.1
-------------

Released on Mar 6th 2013.

Raises :exc:`FloatingPointError` instead of :exc:`ValueError` (math domain
error) for a problem similar to `issue #5`_ but with more extreme input.

Version 0.3
-----------

Released on Mar 5th 2013.

:class:`TrueSkill` got a new option ``backend`` to choose cdf, pdf, ppf
implementation.

When winners have too lower rating than losers, :meth:`TrueSkill.rate` will
raise :exc:`FloatingPointError` if the backend is ``None`` or "scipy". But from
this version, you can avoid the problem with "mpmath" backend. This was
reported at `issue #5`_.

.. _issue #5: https://github.com/sublee/trueskill/issues/5

Version 0.2.1
-------------

Released on Dec 6th 2012.

Fixes a printing bug on :meth:`TrueSkill.quality`.

Version 0.2
-----------

Released on Nov 30th 2012.

- Implements "Partial play".
- Works well in many Python versions, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3 and many
  interpreters, CPython, `Jython`_, `PyPy`_.
- Supports that using dictionaries as a ``rating_group`` to choose specific
  player's rating simply.
- Adds shorcut functions for 2 players individual match, the most usage:
  :func:`rate_1vs1` and :func:`quality_1vs1`,
- :meth:`TrueSkill.transform_ratings` is now called :meth:`TrueSkill.rate`.
- :meth:`TrueSkill.match_quality` is now called :meth:`TrueSkill.quality`.

.. _Jython: http://jython.org/
.. _PyPy: http://pypy.org/

Version 0.1.4
-------------

Released on Oct 5th 2012.

Fixes :exc:`ZeroDivisionError` issue. For more detail, see `issue#3`_. Thanks
to `Yunwon Jeong`_ and `Nikos Kokolakis`_.

.. _issue#3: https://github.com/sublee/trueskill/issues/3
.. _Yunwon Jeong: https://github.com/youknowone
.. _Nikos Kokolakis: https://github.com/konikos

Version 0.1.3
-------------

Released on Mar 10th 2012.

Improves the match quality performance.

Version 0.1.1
-------------

Released on Jan 12th 2012.

Fixes an error in "A" matrix of the match quality algorithm.

Version 0.1
-----------

First public preview release.
