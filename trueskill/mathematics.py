# -*- coding: utf-8 -*-
"""
    trueskill.mathematics
    ~~~~~~~~~~~~~~~~~~~~~

    This module contains basic mathematics functions and objects for TrueSkill
    algorithm. If you have not scipy, this module provides the fallback.

    :copyright: (c) 2012 by Heungsub Lee.
    :license: BSD, see LICENSE for more details.
"""
import copy
import math
try:
    from numbers import Number
except ImportError:
    Number = (int, long, float, complex)

try:
    from scipy.stats import norm
except ImportError:
    from .scipycompat import cdf, pdf, ppf
else:
    cdf, pdf, ppf = norm.cdf, norm.pdf, norm.ppf


__all__ = ['cdf', 'pdf', 'ppf', 'Gaussian', 'Matrix']


class Gaussian(object):
    """A model for the normal distribution."""

    def __init__(self, mu=None, sigma=None, pi=0, tau=0):
        if mu is not None:
            assert sigma != 0, 'A variance(sigma**2) should be greater than 0'
            pi = sigma ** -2
            tau = pi * mu
        self.pi = pi
        self.tau = tau

    @property
    def mu(self):
        """A mean"""
        return self.pi and self.tau / self.pi

    @property
    def sigma(self):
        """A square root of a variance"""
        return math.sqrt(1 / self.pi) if self.pi else float('inf')

    def __mul__(self, other):
        pi, tau = self.pi + other.pi, self.tau + other.tau
        return Gaussian(pi=pi, tau=tau)

    def __truediv__(self, other):
        pi, tau = self.pi - other.pi, self.tau - other.tau
        return Gaussian(pi=pi, tau=tau)

    __div__ = __truediv__  # for Python 2

    def __repr__(self):
        return 'N(mu=%.3f, sigma=%.3f)' % (self.mu, self.sigma)


class Matrix(list):
    """A model for matrix."""

    def __init__(self, src, width=None, height=None):
        if callable(src):
            f, src = src, {}
            size = [width, height]
            if not width:
                def set_width(width):
                    size[0] = width
                size[0] = set_width
            if not height:
                def set_height(height):
                    size[1] = height
                size[1] = set_height
            for (r, c), val in f(*size):
                src[r, c] = val
            width, height = tuple(size)
        if isinstance(src, list):
            is_number = lambda x: isinstance(x, Number)
            unique_col_sizes = set(map(len, src))
            everything_are_number = filter(is_number, sum(src, []))
            if len(unique_col_sizes) != 1 or not everything_are_number:
                raise ValueError('Must be a rectangular array of numbers')
            two_dimensional_array = src
        elif isinstance(src, dict):
            if not width or not height:
                w = h = 0
                for r, c in src.iterkeys():
                    if not width:
                        w = max(w, r + 1)
                    if not height:
                        h = max(h, c + 1)
                if not width:
                    width = w
                if not height:
                    height = h
            two_dimensional_array = []
            for r in range(height):
                row = []
                two_dimensional_array.append(row)
                for c in range(width):
                    row.append(src.get((r, c), 0))
        else:
            raise TypeError('Invalid source')
        super(Matrix, self).__init__(two_dimensional_array)

    @property
    def width(self):
        return len(self[0])

    @property
    def height(self):
        return len(self)

    def transpose(self):
        width, height = self.width, self.height
        src = {}
        for c in range(width):
            for r in range(height):
                src[c, r] = self[r][c]
        return type(self)(src, width=height, height=width)

    def minor(self, row_n, col_n):
        width, height = self.width, self.height
        assert 0 <= row_n < height and 0 <= col_n < width, \
            'Invalid row or column number'
        two_dimensional_array = []
        for r in range(height):
            if r == row_n:
                continue
            row = []
            two_dimensional_array.append(row)
            for c in range(width):
                if c == col_n:
                    continue
                row.append(self[r][c])
        return type(self)(two_dimensional_array)

    def determinant(self):
        width, height = self.width, self.height
        assert width == height, 'Must be a square matrix'
        tmp, rv = copy.deepcopy(self), 1.
        for c in range(width - 1, 0, -1):
            pivot, r = max((abs(tmp[r][c]), r) for r in range(c + 1))
            pivot = tmp[r][c]
            if not pivot:
                return 0.
            tmp[r], tmp[c] = tmp[c], tmp[r]
            if r != c:
                rv = -rv
            rv *= pivot
            fact = -1. / pivot
            for r in range(c):
                f = fact * tmp[r][c]
                for x in range(c):
                    tmp[r][x] += f * tmp[c][x]
        return rv * tmp[0][0]

    def adjugate(self):
        width, height = self.width, self.height
        assert width == height, 'Must be a square matrix'
        if height == 2:
            a, b = self[0][0], self[0][1]
            c, d = self[1][0], self[1][1]
            return type(self)([[d, -b], [-c, a]])
        else:
            src = {}
            for r in range(height):
                for c in range(width):
                    sign = -1 if (r + c) % 2 else 1
                    src[r, c] = self.minor(r, c).determinant() * sign
            return type(self)(src, width, height)

    def inverse(self):
        if self.width == self.height == 1:
            return type(self)([[1. / self[0][0]]])
        else:
            return (1. / self.determinant()) * self.adjugate()

    def __add__(self, other):
        width, height = self.width, self.height
        if (width, height) != (other.width, other.height):
            raise ValueError('Must be same size')
        src = {}
        for r in range(height):
            for c in range(width):
                src[r, c] = self[r][c] + other[r][c]
        return type(self)(src, width, height)

    def __mul__(self, other):
        if self.width != other.height:
            raise ValueError('Bad size')
        width, height = other.width, self.height
        src = {}
        for r in range(height):
            for c in range(width):
                src[r, c] = sum(self[r][x] * other[x][c]
                                for x in range(self.width))
        return type(self)(src, width, height)

    def __rmul__(self, other):
        if not isinstance(other, Number):
            raise TypeError('The operand should be a number')
        width, height = self.width, self.height
        src = {}
        for r in range(height):
            for c in range(width):
                src[r, c] = other * self[r][c]
        return type(self)(src, width, height)

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, super(Matrix, self).__repr__())
