# -*- coding: utf-8 -*-
"""
    trueskill.deprecated
    ~~~~~~~~~~~~~~~~~~~~

    Deprecated features.

    :copyright: (c) 2012-2013 by Heungsub Lee
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from . import Rating, expose, global_env, rate_1vs1, quality_1vs1, DELTA


__all__ = ['transform_ratings', 'match_quality', 'dynamic_draw_probability',
           'ensure_backward_compatibility']


# deprecated functions


def transform_ratings(rating_groups, ranks=None, min_delta=DELTA):
    return global_env().transform_ratings(rating_groups, ranks, min_delta)


def match_quality(rating_groups):
    return global_env().match_quality(rating_groups)


def dynamic_draw_probability(rating1, rating2, env=None):
    """Deprecated. It was an approximation for :func:`quality_1vs1`.

    .. deprecated:: 0.4.1
       Use :func:`quality_1vs1` instead.
    """
    from warnings import warn
    warn('Use quality_1vs1 instead', DeprecationWarning)
    return quality_1vs1(rating1, rating2, env=env)


# deprecated methods


def addattr(obj, attr, value):
    if hasattr(obj, attr):
        raise AttributeError('The attribute already exists')
    return setattr(obj, attr, value)


def ensure_backward_compatibility(TrueSkill, Rating):
    addattr(TrueSkill, 'Rating', TrueSkill_Rating)
    addattr(TrueSkill, 'transform_ratings', TrueSkill_transform_ratings)
    addattr(TrueSkill, 'match_quality', TrueSkill_match_quality)
    addattr(TrueSkill, 'rate_1vs1', TrueSkill_rate_1vs1)
    addattr(TrueSkill, 'quality_1vs1', TrueSkill_quality_1vs1)
    addattr(Rating, 'exposure', Rating_exposure)


def TrueSkill_Rating(self, mu=None, sigma=None):
    """Deprecated. Used to create a :class:`Rating` object.

    .. deprecated:: 0.2
       Override :meth:`create_rating` instead.
    """
    from warnings import warn
    warn('TrueSkill.Rating is now called TrueSkill.create_rating',
         DeprecationWarning)
    return self.create_rating(mu, sigma)


def TrueSkill_transform_ratings(self, rating_groups, ranks=None,
                                min_delta=DELTA):
    """Deprecated. Used to rate the given ratings.

    .. deprecated:: 0.2
       Override :meth:`rate` instead.
    """
    from warnings import warn
    warn('TrueSkill.transform_ratings is now called TrueSkill.rate',
         DeprecationWarning)
    rating_groups = [(r,) if isinstance(r, Rating) else r
                     for r in rating_groups]
    return self.rate(rating_groups, ranks, min_delta=min_delta)


def TrueSkill_match_quality(self, rating_groups):
    """Deprecated. Used to calculate a match quality.

    .. deprecated:: 0.2
       Override :meth:`quality` instead.
    """
    from warnings import warn
    warn('TrueSkill.match_quality is now called TrueSkill.quality',
         DeprecationWarning)
    rating_groups = [(r,) if isinstance(r, Rating) else r
                     for r in rating_groups]
    return self.quality(rating_groups)


def TrueSkill_rate_1vs1(self, rating1, rating2, drawn=False, min_delta=DELTA):
    """Deprecated. Used to rate just a head-to-haed match.

    .. deprecated:: 0.4
       Use :func:`rate_1vs1` instead.
    """
    from warnings import warn
    warn('Use rate_1vs1, a normal function instead', DeprecationWarning)
    return rate_1vs1(rating1, rating2, drawn, min_delta, self)


def TrueSkill_quality_1vs1(self, rating1, rating2):
    """Deprecated. Used to calculate a match quality for a head-to-haed match.

    .. deprecated:: 0.4
       Use :func:`quality_1vs1` instead.
    """
    from warnings import warn
    warn('Use quality_1vs1, a normal function instead', DeprecationWarning)
    return quality_1vs1(rating1, rating2, self)


@property
def Rating_exposure(self):
    """Deprecated. Used to get a value that will go up on the whole.

    .. deprecated:: 0.4
       Use :meth:`TrueSkill.expose` instead.
    """
    from warnings import warn
    warn('Use TrueSkill.expose instead', DeprecationWarning)
    return expose(self)
