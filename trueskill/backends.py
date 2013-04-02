# -*- coding: utf-8 -*-
"""
    trueskill.backends
    ~~~~~~~~~~~~~~~~~~

    Provides mathematical statistics backend chooser.

    :copyright: (c) 2012-2013 by Heungsub Lee.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import
import math


__all__ = ['available_backends', 'choose_backend', 'cdf', 'pdf', 'ppf']


def _gen_erfcinv(erfc, math=math):
    """Generates the inverse function of erfc by the given erfc function and
    math module.
    """
    def erfcinv(y):
        """The inverse function of erfc."""
        if y >= 2:
            return -100.
        elif y <= 0:
            return 100.
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
    return erfcinv


def _gen_ppf(erfc, math=math):
    """ppf is the inverse function of cdf. This function generates cdf by the
    given erfc and math module.
    """
    erfcinv = _gen_erfcinv(erfc, math)
    def ppf(x, mu=0, sigma=1):
        """The inverse function of cdf."""
        return mu - sigma * math.sqrt(2) * erfcinv(2 * x)
    return ppf


def erfc(x):
    """Complementary error function (via `http://bit.ly/zOLqbc`_)"""
    z = abs(x)
    t = 1. / (1. + z / 2.)
    r = t * math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (
                     0.37409196 + t * (0.09678418 + t * (
                     -0.18628806 + t * (0.27886807 + t * (
                     -1.13520398 + t * (1.48851587 + t * (
                     -0.82215223 + t * 0.17087277)))))))))
    return 2. - r if x < 0 else r


def cdf(x, mu=0, sigma=1):
    """Cumulative distribution function"""
    return 0.5 * erfc(-(x - mu) / (sigma * math.sqrt(2)))


def pdf(x, mu=0, sigma=1):
    """Probability density function"""
    return (1 / math.sqrt(2 * math.pi) * abs(sigma) *
            math.exp(-(((x - mu) / abs(sigma)) ** 2 / 2)))


ppf = _gen_ppf(erfc)


def choose_backend(backend):
    """Returns a tuple containing cdf, pdf, ppf from the chosen backend.

    >>> cdf, pdf, ppf = choose_backend(None)
    >>> cdf(-10)
    7.619853263532764e-24
    >>> cdf, pdf, ppf = choose_backend('mpmath')
    >>> cdf(-10)
    mpf('7.6198530241605255e-24')

    .. versionadded:: 0.3
    """
    if backend is None:  # fallback
        return cdf, pdf, ppf
    elif backend == 'mpmath':
        try:
            import mpmath
        except ImportError:
            raise ImportError('Install "mpmath" to use this backend')
        return mpmath.ncdf, mpmath.npdf, _gen_ppf(mpmath.erfc, math=mpmath)
    elif backend == 'scipy':
        try:
            from scipy.stats import norm
        except ImportError:
            raise ImportError('Install "scipy" to use this backend')
        return norm.cdf, norm.pdf, norm.ppf
    raise ValueError('%r backend is not defined' % backend)


def available_backends():
    """Detects list of available backends. All of defined backends are ``None``
    -- internal implementation, "mpmath", "scipy".

    You can check if the backend is available in the current environment with
    this function::

       if 'mpmath' in available_backends():
           # mpmath can be used in the current environment
           setup(backend='mpmath')

    .. versionadded:: 0.3
    """
    backends = [None]
    for backend in ['mpmath', 'scipy']:
        try:
            __import__(backend)
        except ImportError:
            continue
        backends.append(backend)
    return backends
