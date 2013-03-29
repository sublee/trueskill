# -*- coding: utf-8 -*-
"""
    trueskill.mathematics
    ~~~~~~~~~~~~~~~~~~~~~

    This module contains basic mathematics functions and objects for TrueSkill
    algorithm. If you have not scipy, this module provides the fallback.

    :copyright: (c) 2012-2013 by Heungsub Lee.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import
import copy
import math
try:
    from numbers import Number
except ImportError:
    Number = (int, long, float, complex)


__all__ = ['Gaussian', 'Matrix', 'inf']


inf = float('inf')


class Gaussian(object):
    """A model for the normal distribution."""

    #: Precision, the inverse of the variance.
    pi = 0
    #: Precision adjusted mean, the precision multiplied by the mean.
    tau = 0

    def __init__(self, mu=None, sigma=None, pi=0, tau=0):
        if mu is not None:
            if sigma is None:
                raise TypeError('sigma argument is needed')
            elif sigma == 0:
                raise ValueError('sigma**2 should be greater than 0')
            pi = sigma ** -2
            tau = pi * mu
        self.pi = pi
        self.tau = tau

    @property
    def mu(self):
        """A property which returns the mean."""
        return self.pi and self.tau / self.pi

    @property
    def sigma(self):
        """A property which returns the the square root of the variance."""
        return math.sqrt(1 / self.pi) if self.pi else inf

    def __mul__(self, other):
        pi, tau = self.pi + other.pi, self.tau + other.tau
        return Gaussian(pi=pi, tau=tau)

    def __truediv__(self, other):
        pi, tau = self.pi - other.pi, self.tau - other.tau
        return Gaussian(pi=pi, tau=tau)

    __div__ = __truediv__  # for Python 2

    def __eq__(self, other):
        return self.pi == other.pi and self.tau == other.tau

    def __lt__(self, other):
        return self.mu < other.mu

    def __le__(self, other):
        return self.mu <= other.mu

    def __gt__(self, other):
        return self.mu > other.mu

    def __ge__(self, other):
        return self.mu >= other.mu

    def __repr__(self):
        return 'N(mu=%.3f, sigma=%.3f)' % (self.mu, self.sigma)

    def _repr_latex_(self):
        latex = r'\mathcal{ N }( %.3f, %.3f^2 )' % (self.mu, self.sigma)
        return '$%s$' % latex


class Matrix(list):
    """A model for matrix."""

    def __init__(self, src, height=None, width=None):
        if callable(src):
            f, src = src, {}
            size = [height, width]
            if not height:
                def set_height(height):
                    size[0] = height
                size[0] = set_height
            if not width:
                def set_width(width):
                    size[1] = width
                size[1] = set_width
            try:
                for (r, c), val in f(*size):
                    src[r, c] = val
            except TypeError:
                raise TypeError('A callable src must return an interable '
                                'which generates a tuple containing '
                                'coordinate and value')
            height, width = tuple(size)
            if height is None or width is None:
                raise TypeError('A callable src must call set_height and '
                                'set_width if the size is non-deterministic')
        if isinstance(src, list):
            is_number = lambda x: isinstance(x, Number)
            unique_col_sizes = set(map(len, src))
            everything_are_number = filter(is_number, sum(src, []))
            if len(unique_col_sizes) != 1 or not everything_are_number:
                raise ValueError('src must be a rectangular array of numbers')
            two_dimensional_array = src
        elif isinstance(src, dict):
            if not height or not width:
                w = h = 0
                for r, c in src.iterkeys():
                    if not height:
                        h = max(h, r + 1)
                    if not width:
                        w = max(w, c + 1)
                if not height:
                    height = h
                if not width:
                    width = w
            two_dimensional_array = []
            for r in range(height):
                row = []
                two_dimensional_array.append(row)
                for c in range(width):
                    row.append(src.get((r, c), 0))
        else:
            raise TypeError('src must be a list or dict or callable')
        super(Matrix, self).__init__(two_dimensional_array)

    @property
    def height(self):
        return len(self)

    @property
    def width(self):
        return len(self[0])

    def transpose(self):
        height, width = self.height, self.width
        src = {}
        for c in range(width):
            for r in range(height):
                src[c, r] = self[r][c]
        return type(self)(src, height=width, width=height)

    def minor(self, row_n, col_n):
        height, width = self.height, self.width
        if not (0 <= row_n < height):
            raise ValueError('row_n should be between 0 and %d' % height)
        elif not (0 <= col_n < width):
            raise ValueError('col_n should be between 0 and %d' % width)
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
        height, width = self.height, self.width
        if height != width:
            raise ValueError('Only square matrix can calculate a determinant')
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
        height, width = self.height, self.width
        if height != width:
            raise ValueError('Only square matrix can be adjugated')
        if height == 2:
            a, b = self[0][0], self[0][1]
            c, d = self[1][0], self[1][1]
            return type(self)([[d, -b], [-c, a]])
        src = {}
        for r in range(height):
            for c in range(width):
                sign = -1 if (r + c) % 2 else 1
                src[r, c] = self.minor(r, c).determinant() * sign
        return type(self)(src, height, width)

    def inverse(self):
        if self.height == self.width == 1:
            return type(self)([[1. / self[0][0]]])
        return (1. / self.determinant()) * self.adjugate()

    def __add__(self, other):
        height, width = self.height, self.width
        if (height, width) != (other.height, other.width):
            raise ValueError('Must be same size')
        src = {}
        for r in range(height):
            for c in range(width):
                src[r, c] = self[r][c] + other[r][c]
        return type(self)(src, height, width)

    def __mul__(self, other):
        if self.width != other.height:
            raise ValueError('Bad size')
        height, width = self.height, other.width
        src = {}
        for r in range(height):
            for c in range(width):
                src[r, c] = sum(self[r][x] * other[x][c]
                                for x in range(self.width))
        return type(self)(src, height, width)

    def __rmul__(self, other):
        if not isinstance(other, Number):
            raise TypeError('The operand should be a number')
        height, width = self.height, self.width
        src = {}
        for r in range(height):
            for c in range(width):
                src[r, c] = other * self[r][c]
        return type(self)(src, height, width)

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, super(Matrix, self).__repr__())

    def _repr_latex_(self):
        rows = [' && '.join(['%.3f' % cell for cell in row]) for row in self]
        latex = r'\begin{matrix} %s \end{matrix}' % r'\\'.join(rows)
        return '$%s$' % latex
