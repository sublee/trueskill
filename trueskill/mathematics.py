import math


#__all__ = 'cdf', 'pdf', 'ppf', 'Gaussian'


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
    """A model for normal distribution."""

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


class Matrix(object):

    def __init__(self, rows=None, cols=None):
        assert rows is cols is None or not rows is bool(cols)
        self.rows = []
        if rows:
            for x, row in enumerate(rows):
                for y, col in enumerate(row):
                    self[x][y] = col
        elif cols:
            for y, col in enumerate(cols):
                for x, row in enumerate(col):
                    self[x][y] = row

    @property
    def width(self):
        w = 0
        for row in self:
            w = max(w, len(row))
        return w

    @property
    def height(self):
        return len(self.rows)

    def get_cofactor(self, del_x, del_y):
        return (-1 if (del_x + del_y) % 2 else 1) * \
               self.get_minor(del_x, del_y).determinant

    def get_minor(self, del_x, del_y):
        rv = Matrix()
        for x in xrange(self.height):
            for y in xrange(self.width):
                rv[x][y] = 0 if x == del_x and y == del_y else self[x][y]
        return rv

    @property
    def determinant(self):
        assert self.width == self.height
        if self.height == 1:
            return self[0][0]
        elif self.height == 2:
            a, b = self[0][0], self[0][1]
            c, d = self[1][0], self[1][1]
            return a * d - b * c
        rv = 0
        for y in xrange(self.width):
            rv += self[0][y] * self.get_cofactor(0, y)
        return rv

    @property
    def adjugate(self):
        assert self.width == self.height
        if self.height == 2:
            a, b = self[0][0], self[0][1]
            c, d = self[1][0], self[1][1]
            return type(self)([[d, -b], [-c, a]])
        else:
            rv = type(self)()
            for x in xrange(self.height):
                for y in xrange(self.width):
                    rv[y][x] = self.get_cofactor(x, y)
            return rv

    @property
    def inverse(self):
        if self.width == self.height == 1:
            return type(self)([[1. / self[0][0]]])
        else:
            return (1. / self.determinant) * self.adjugate

    def __iter__(self):
        return iter(Row(row) for row in self.rows)

    def __getitem__(self, x):
        if len(self.rows) <= x:
            for _ in xrange(len(self.rows), x + 1):
                self.rows.append([])
        return Row(self.rows[x])

    def __add__(self, other):
        assert isinstance(other, type(self))
        assert self.width == other.width and self.height == other.height
        rv = type(self)()
        for x in xrange(self.height):
            for y in xrange(self.width):
                rv[x][y] = self[x][y] + other[x][y]
        return rv

    def __mul__(self, other):
        """Matrix multiplication."""
        assert isinstance(other, type(self))
        rv = type(self)()
        height = self.height
        width = other.width
        for x in xrange(height):
            for y in xrange(width):
                product_value = 0
                for i in xrange(self.width):
                    product_value += self[x][i] * other[i][y]
                rv[x][y] = product_value
        return rv

    def __rmul__(self, other):
        """Scalar multiplication."""
        from numbers import Number
        assert isinstance(other, Number)
        rv = type(self)()
        height = self.height
        width = self.width
        for x in xrange(height):
            for y in xrange(width):
                rv[x][y] = self[x][y] * other
        return rv

    def __repr__(self):
        col_size = 7
        line = ('+' + '-' * col_size) * self.width + '+'
        rv = line + '\n'
        for row in self.rows:
            for x in xrange(self.width):
                rv += '|'
                try:
                    if row[x] is None:
                        raise IndexError
                    r = repr(row[x]).rjust(col_size)
                    if len(r) > col_size:
                        r = r[:col_size]
                    rv += r
                except IndexError:
                    rv += ' ' * (col_size - 1) + '-'
            rv += '|\n'
        rv += line
        return rv


class Row(object):

    def __init__(self, ref):
        self.ref = ref

    def __getitem__(self, y):
        if len(self.ref) <= y:
            for _ in xrange(len(self.ref), y + 1):
                self.ref.append(0)
        return self.ref[y]

    def __setitem__(self, y, val):
        self.__getitem__(y)
        self.ref[y] = val

    def __len__(self):
        return len(self.ref)
