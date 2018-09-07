Version 0.4.5
-------------

Released on Sep 7 2018.

Started to support Python 3.6 and 3.7. But dropped support of Python 2.5, 2.6,
3.1, 3.2, and 3.3.  Thanks to `Hugo`_.

.. _Hugo: https://github.com/hugovk

Version 0.4.4
-------------

Released on Dec 31 2015.

Fixed documentation error.  See `issue #11`_.  Thanks to `Russel Simmons`_.

.. _issue #11: https://github.com/sublee/trueskill/issues/11
.. _Russel Simmons: https://github.com/rsimmons

Version 0.4.3
-------------

Released on Sep 4 2014.

Fixed ordering bug on weights argument as a dict.  This was reported at
`issue #9`_.

.. _issue #9: https://github.com/sublee/trueskill/issues/9

Version 0.4.2
-------------

Released on Jun 13 2014.

Updated only meta code such as :file:`setup.py`.

Version 0.4.1
-------------

Released on Jun 6 2013.

Deprecated :func:`dynamic_draw_probability`.

Version 0.4
-----------

Released on Mar 25 2013.

- Added dynamic draw probability.
- Replaced :meth:`Rating.exposure` with :meth:`TrueSkill.expose`.  Because the
  TrueSkill settings have to adjust a fomula to calculate an exposure.
- Deprecated head-to-head shortcut methods in :class:`TrueSkill`.  The
  top-level shortcut functions are still alive.

Version 0.3.1
-------------

Released on Mar 6 2013.

Changed to raise :exc:`FloatingPointError` instead of :exc:`ValueError` (math
domain error) for a problem similar to `issue #5`_ but with more extreme input.

Version 0.3
-----------

Released on Mar 5 2013.

:class:`TrueSkill` got a new option ``backend`` to choose cdf, pdf, ppf
implementation.

When winners have too lower rating than losers, :meth:`TrueSkill.rate` will
raise :exc:`FloatingPointError` if the backend is ``None`` or "scipy".  But
from this version, you can avoid the problem with "mpmath" backend.  This was
reported at `issue #5`_.

.. _issue #5: https://github.com/sublee/trueskill/issues/5

Version 0.2.1
-------------

Released on Dec 6 2012.

Fixed a printing bug on :meth:`TrueSkill.quality`.

Version 0.2
-----------

Released on Nov 30 2012.

- Added "Partial play" implementation.
- Worked well in many Python versions, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3 and many
  interpreters, CPython, `Jython`_, `PyPy`_.
- Supported that using dictionaries as a ``rating_group`` to choose specific
  player's rating simply.
- Added shorcut functions for 2 players individual match, the most usage:
  :func:`rate_1vs1` and :func:`quality_1vs1`,
- Renamed :meth:`TrueSkill.transform_ratings` to :meth:`TrueSkill.rate`.
- Renamed :meth:`TrueSkill.match_quality` to :meth:`TrueSkill.quality`.

.. _Jython: http://jython.org/
.. _PyPy: http://pypy.org/

Version 0.1.4
-------------

Released on Oct 5 2012.

Fixed :exc:`ZeroDivisionError` issue.  For more detail, see `issue#3`_.  Thanks
to `Yunwon Jeong`_ and `Nikos Kokolakis`_.

.. _issue#3: https://github.com/sublee/trueskill/issues/3
.. _Yunwon Jeong: https://github.com/youknowone
.. _Nikos Kokolakis: https://github.com/konikos

Version 0.1.3
-------------

Released on Mar 10 2012.

Improved the match quality performance.

Version 0.1.1
-------------

Released on Jan 12 2012.

Fixed an error in "A" matrix of the match quality algorithm.

Version 0.1
-----------

First public preview release.
