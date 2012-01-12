import math
from numbers import Number


__all__ = 'cdf', 'pdf', 'ppf', 'Gaussian', 'Matrix'


try:
    from scipy.stats import norm
    cdf, pdf, ppf = norm.cdf, norm.pdf, norm.ppf
except ImportError:

    def erfcc(x):
        """Complementary error function (via http://bit.ly/zOLqbc)"""
        z = abs(x)
        t = 1. / (1. + z / 2.)
        r = t * math.exp(-z * z - 1.26551223 + \
            t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + \
            t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + \
            t * (1.48851587 + t * (-0.82215223 + t * 0.17087277)))))))))
        return 2. - r if x < 0 else r

    def ierfcc(y):
        """The inverse function of erfcc"""
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
            err = erfcc(x) - y
            x += err / (1.12837916709551257 * math.exp(-(x ** 2)) - x * err)
        return x if zero_point else -x

    def cdf(x):
        """Cumulative distribution function"""
        return 1 - 0.5 * erfcc(x / math.sqrt(2))

    def pdf(x):
        """Probability density function"""
        return (1 / math.sqrt(2 * math.pi)) * math.exp(-(x ** 2 / 2))

    def ppf(x):
        """The inverse function of CDF"""
        return -math.sqrt(2) * ierfcc(2 * x)


class Gaussian(object):
    """A model for the normal distribution."""

    def __init__(self, mu=None, sigma=None, pi=0, tau=0):
        if mu is not None:
            assert sigma != 0, 'a variance(sigma^2) should be greater than 0'
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

    def __div__(self, other):
        pi, tau = self.pi - other.pi, self.tau - other.tau
        return Gaussian(pi=pi, tau=tau)

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
            msg = 'must be a rectangular array of numbers'
            assert len(unique_col_sizes) == 1, msg
            assert all(map(is_number, sum(src, []))), msg
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
            for r in xrange(height):
                row = []
                two_dimensional_array.append(row)
                for c in xrange(width):
                    row.append(src.get((r, c), 0))
        else:
            raise TypeError('invalid source')
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
        for c in xrange(width):
            for r in xrange(height):
                src[c, r] = self[r][c]
        return type(self)(src, width=height, height=width)

    def cofactor(self, row_n, col_n):
        return (-1 if (row_n + col_n) % 2 else 1) * \
               self.minor(row_n, col_n).determinant()

    def minor(self, row_n, col_n):
        width, height = self.width, self.height
        assert 0 <= row_n < height and 0 <= col_n < width, \
               'invalid row or column number'
        two_dimensional_array = []
        for r in xrange(height):
            if r == row_n:
                continue
            row = []
            two_dimensional_array.append(row)
            for c in xrange(width):
                if c == col_n:
                    continue
                row.append(self[r][c])
        return type(self)(two_dimensional_array)

    def determinant(self):
        width, height = self.width, self.height
        assert width == height, 'must be a square matrix'
        if height == 1:
            return self[0][0]
        elif height == 2:
            a, b = self[0][0], self[0][1]
            c, d = self[1][0], self[1][1]
            return a * d - b * c
        else:
            return sum(self[0][c] * self.cofactor(0, c) \
                       for c in xrange(width))

    def adjugate(self):
        width, height = self.width, self.height
        assert width == height, 'must be a square matrix'
        if height == 2:
            a, b = self[0][0], self[0][1]
            c, d = self[1][0], self[1][1]
            return type(self)([[d, -b], [-c, a]])
        else:
            src = {}
            for r in xrange(height):
                for c in xrange(width):
                    src[r, c] = self.cofactor(r, c)
            return type(self)(src, width, height)

    def inverse(self):
        if self.width == self.height == 1:
            return type(self)([[1. / self[0][0]]])
        else:
            return (1. / self.determinant()) * self.adjugate()

    def __add__(self, other):
        width, height = self.width, self.height
        assert (width, height) == (other.width, other.height), \
               'must be same size'
        src = {}
        for r in xrange(height):
            for c in xrange(width):
                src[r, c] = self[r][c] + other[r][c]
        return type(self)(src, width, height)

    def __mul__(self, other):
        assert self.width == other.height, 'bad size'
        width, height = other.width, self.height
        src = {}
        for r in xrange(height):
            for c in xrange(width):
                src[r, c] = sum(self[r][x] * other[x][c] \
                                for x in xrange(self.width))
        return type(self)(src, width, height)

    def __rmul__(self, other):
        assert isinstance(other, Number)
        width, height = self.width, self.height
        src = {}
        for r in xrange(height):
            for c in xrange(width):
                src[r, c] = other * self[r][c]
        return type(self)(src, width, height)

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, super(Matrix, self).__repr__())
