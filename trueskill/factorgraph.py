from __future__ import absolute_import

from math import sqrt

from .mathematics import cdf, pdf, ppf, Gaussian


class Node(object):

    pass


class Variable(Node, Gaussian):

    def __init__(self):
        self.messages = {}
        super(Variable, self).__init__()

    def set(self, val):
        delta = self.delta(val)
        self.pi, self.tau = val.pi, val.tau
        return delta

    def delta(self, other):
        return max(abs(self.tau - other.tau), sqrt(abs(self.pi - other.pi)))

    def update_message(self, factor, pi=0, tau=0, message=None):
        message = message or Gaussian(pi=pi, tau=tau)
        old_message, self[factor] = self[factor], message
        return self.set(self / old_message * message)

    def update_value(self, factor, pi=0, tau=0, value=None):
        value = value or Gaussian(pi=pi, tau=tau)
        old_message = self[factor]
        self[factor] = value * old_message / self
        return self.set(value)

    def __getitem__(self, factor):
        return self.messages[factor]

    def __setitem__(self, factor, message):
        self.messages[factor] = message

    def __repr__(self):
        args = (type(self).__name__, super(Variable, self).__repr__(),
                len(self.messages), '' if len(self.messages) == 1 else 's')
        return '<%s %s with %d connection%s>' % args


class Factor(Node):

    def __init__(self, vars):
        self.vars = vars
        for var in vars:
            var[self] = Gaussian()

    def down(self):
        pass

    def up(self):
        pass

    @property
    def var(self):
        assert len(self.vars) == 1
        return self.vars[0]

    def __repr__(self):
        args = (type(self).__name__, len(self.vars), \
                '' if len(self.vars) == 1 else 's')
        return '<%s with %d connection%s>' % args


class PriorFactor(Factor):

    def __init__(self, var, val, dynamic=0):
        super(PriorFactor, self).__init__([var])
        self.val = val
        self.dynamic = dynamic

    def down(self):
        sigma = sqrt(self.val.sigma ** 2 + self.dynamic ** 2)
        value = Gaussian(self.val.mu, sigma)
        return self.var.update_value(self, value=value)


class LikelihoodFactor(Factor):

    def __init__(self, mean_var, value_var, variance):
        super(LikelihoodFactor, self).__init__([mean_var, value_var])
        self.mean = mean_var
        self.value = value_var
        self.variance = variance

    def down(self): # update value
        val = self.mean
        msg = val / self.mean[self]
        pi = 1. / self.variance
        a = pi / (pi + val.pi)
        return self.value.update_message(self, a * msg.pi, a * msg.tau)

    def up(self): # update mean
        val = self.value
        msg = val / self.value[self]
        a = 1. / (1 + self.variance * msg.pi)
        return self.mean.update_message(self, a * msg.pi, a * msg.tau)


class SumFactor(Factor):

    def __init__(self, sum_var, term_vars, coeffs):
        super(SumFactor, self).__init__([sum_var] + term_vars)
        self.sum = sum_var
        self.terms = term_vars
        self.coeffs = coeffs

    def down(self):
        vals = self.terms
        msgs = [var[self] for var in vals]
        return self.update(self.sum, vals, msgs, self.coeffs)

    def up(self, index=0):
        coeff = self.coeffs[index]
        #for index, coeff in enumerate(self.coeffs):
        coeffs = [-c / coeff for x, c in enumerate(self.coeffs) \
                             if x != index]
        coeffs.insert(index, 1. / coeff)
        vals = self.terms[:]
        vals[index] = self.sum
        msgs = [var[self] for var in vals]
        return self.update(self.terms[index], vals, msgs, coeffs)

    def update(self, var, vals, msgs, coeffs):
        '''
        size = len(coeffs)
        pi = 1. / sum(coeffs[x] ** 2 / (vals[x].pi - msgs[x].pi) for x in xrange(size))
        tau = pi * sum(coeffs[x] * (vals[x].tau - msgs[x].tau) / (vals[x].pi - msgs[x].pi) for x in xrange(size))
        '''
        size = len(coeffs)
        divs = [vals[x] / msgs[x] for x in xrange(size)]
        pi = 1. / sum(coeffs[x] ** 2 / divs[x].pi for x in xrange(size))
        tau = pi * sum(coeffs[x] * divs[x].mu for x in xrange(size))
        return var.update_message(self, pi, tau)


class TruncateFactor(Factor):

    def __init__(self, var, v_func, w_func, draw_margin):
        super(TruncateFactor, self).__init__([var])
        self.v_func = v_func
        self.w_func = w_func
        self.draw_margin = draw_margin

    def up(self):
        val = self.var
        msg = self.var[self]
        div = val / msg
        sqrt_pi = sqrt(div.pi)
        args = (div.tau / sqrt_pi, self.draw_margin * sqrt_pi)
        v = self.v_func(*args)
        w = self.w_func(*args)
        denom = (1. - w)
        return self.var.update_value(self, div.pi / denom,
                                     (div.tau + sqrt_pi * v) / denom)
