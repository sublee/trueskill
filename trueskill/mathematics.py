import math


__all__ = 'cdf', 'pdf', 'ppf', 'Gaussian'


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
