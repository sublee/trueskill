# -*- coding: utf-8 -*-
"""
    trueskill.statistics
    ~~~~~~~~~~~~~~~~~~~~

    Provides mathematical statistics implement chooser.

    Available implements:

    - ``None`` (default)
    - scipy_
    - mpmath_

    .. _scipy: http://www.scipy.org/
    .. _mpmath: https://code.google.com/p/mpmath

    :copyright: (c) 2012-2013 by Heungsub Lee.
    :license: BSD, see LICENSE for more details.
"""
import functools
import math


__all__ = ['available_implements', 'choose_implement', 'cdf', 'pdf', 'ppf']


def erfc(x):
    """Complementary error function (via http://bit.ly/zOLqbc)"""
    z = abs(x)
    t = 1. / (1. + z / 2.)
    r = t * math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (
                     0.37409196 + t * (0.09678418 + t * (
                     -0.18628806 + t * (0.27886807 + t * (
                     -1.13520398 + t * (1.48851587 + t * (
                     -0.82215223 + t * 0.17087277)))))))))
    return 2. - r if x < 0 else r


def erfcinv(y, erfc=erfc):
    """The inverse function of erfc"""
    if y >= 2:
        return -100
    elif y <= 0:
        return 100
    zero_point = y < 1
    if not zero_point:
        y = 2 - y
    t = math.sqrt(-2 * math.log(y / 2.))
    x = -0.70711 * \
        ((2.30753 + t * 0.27061) / (1. + t * (0.99229 + t * 0.04481)) - t)
    for i in xrange(2):
        err = erfc(x) - y
        x += err / (1.12837916709551257 * math.exp(-(x ** 2)) - x * err)
    return x if zero_point else -x


def cdf(x, mu=0, sigma=1):
    """Cumulative distribution function"""
    return 0.5 * erfc(-(x - mu) / (sigma * math.sqrt(2)))


def pdf(x, mu=0, sigma=1):
    """Probability density function"""
    return (1 / math.sqrt(2 * math.pi) * abs(sigma) *
            math.exp(-(((x - mu) / abs(sigma)) ** 2 / 2)))


def ppf(x, mu=0, sigma=1):
    """The inverse function of CDF"""
    return mu - sigma * math.sqrt(2) * erfcinv(2 * x)


def available_implements():
    implements = [None]
    for name in ['mpmath', 'scipy']:
        try:
            __import__(name)
        except ImportError:
            continue
        implements.append(name)
    return implements


def choose_implement(name):
    if name is None:  # fallback
        return cdf, pdf, ppf
    elif name == 'mpmath':
        import mpmath
        mpmath_erfcinv = functools.partial(erfcinv, erfc=mpmath.erfc)
        def mpmath_ppf(x, mu=0, sigma=1):
            return (mu - sigma * mpmath.sqrt(2) * mpmath_erfcinv(2 * x))
        return mpmath.ncdf, mpmath.npdf, mpmath_ppf
    elif name == 'scipy':
        from scipy.stats import norm
        return norm.cdf, norm.pdf, norm.ppf
    raise ValueError('Unknown statistics implement: %r' % name)
