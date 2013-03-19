# -*- coding: utf-8 -*-
"""
    trueskill.deprecated
    ~~~~~~~~~~~~~~~~~~~~

    Deprecated features.

    :copyright: (c) 2012-2013 by Heungsub Lee
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from . import Rating, expose, global_env, DELTA


__all__ = ['transform_ratings', 'match_quality',
           'ensure_backward_compatibility']


# deprecated functions


def transform_ratings(rating_groups, ranks=None, min_delta=DELTA):
    return global_env().transform_ratings(rating_groups, ranks, min_delta)


def match_quality(rating_groups):
    return global_env().match_quality(rating_groups)


# deprecated methods


def addattr(obj, attr, value):
    if hasattr(obj, attr):
        raise AttributeError('The attribute already exists')
    return setattr(obj, attr, value)


def ensure_backward_compatibility(TrueSkill, Rating):
    addattr(TrueSkill, 'Rating', TrueSkill_Rating)
    addattr(TrueSkill, 'transform_ratings', TrueSkill_transform_ratings)
    addattr(TrueSkill, 'match_quality', TrueSkill_match_quality)
    addattr(Rating, 'exposure', Rating_exposure)


def TrueSkill_Rating(self, mu=None, sigma=None):
    """Deprecated. Used to create a :class:`Rating` object.

    .. deprecated:: 0.2
       This method is deprecated with 0.2. Override :meth:`create_rating`
       instead.
    """
    from warnings import warn
    warn('TrueSkill.Rating is now called TrueSkill.create_rating',
         DeprecationWarning)
    return self.create_rating(mu, sigma)


def TrueSkill_transform_ratings(self, rating_groups, ranks=None,
                                min_delta=DELTA):
    """Deprecated. Used to rate the given ratings.

    .. deprecated:: 0.2
       This method is deprecated with 0.2. Override :meth:`rate` instead.
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
       This method is deprecated with 0.2. Override :meth:`quality`
       instead.
    """
    from warnings import warn
    warn('TrueSkill.match_quality is now called TrueSkill.quality',
         DeprecationWarning)
    rating_groups = [(r,) if isinstance(r, Rating) else r
                     for r in rating_groups]
    return self.quality(rating_groups)


@property
def Rating_exposure(self):
    """Deprecated. Used to get a value that will go up on the whole.

    .. deprecated:: 0.4
       This method is deprecated with 0.4. Use :meth:`TrueSkill.expose`
       instead.
    """
    from warnings import warn
    warn('Use TrueSkill.expose instead', DeprecationWarning)
    return expose(self)
