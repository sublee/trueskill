# -*- coding: utf-8 -*-
"""
    trueskill.factorgraph
    ~~~~~~~~~~~~~~~~~~~~~

    This module contains nodes for the factor graph of TrueSkill algorithm.

    :copyright: (c) 2012-2013 by Heungsub Lee.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import
import itertools
import math

from .mathematics import Gaussian, inf


__all__ = ['Variable', 'PriorFactor', 'LikelihoodFactor', 'SumFactor',
           'TruncateFactor']


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
        pi_delta = abs(self.pi - other.pi)
        if pi_delta == inf:
            return 0.
        return max(abs(self.tau - other.tau), math.sqrt(pi_delta))

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
        return 0

    def up(self):
        return 0

    @property
    def var(self):
        assert len(self.vars) == 1
        return self.vars[0]

    def __repr__(self):
        args = (type(self).__name__, len(self.vars),
                '' if len(self.vars) == 1 else 's')
        return '<%s with %d connection%s>' % args


class PriorFactor(Factor):

    def __init__(self, var, val, dynamic=0):
        super(PriorFactor, self).__init__([var])
        self.val = val
        self.dynamic = dynamic

    def down(self):
        sigma = math.sqrt(self.val.sigma ** 2 + self.dynamic ** 2)
        value = Gaussian(self.val.mu, sigma)
        return self.var.update_value(self, value=value)


class LikelihoodFactor(Factor):

    def __init__(self, mean_var, value_var, variance):
        super(LikelihoodFactor, self).__init__([mean_var, value_var])
        self.mean = mean_var
        self.value = value_var
        self.variance = variance

    def down(self):
        # update value
        val = self.mean
        msg = val / self.mean[self]
        pi = 1. / self.variance
        a = pi / (pi + val.pi)
        return self.value.update_message(self, a * msg.pi, a * msg.tau)

    def up(self):
        # update mean
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
        coeffs = []
        for x, c in enumerate(self.coeffs):
            try:
                if x == index:
                    coeffs.append(1. / coeff)
                else:
                    coeffs.append(-c / coeff)
            except ZeroDivisionError:
                coeffs.append(0.)
        vals = self.terms[:]
        vals[index] = self.sum
        msgs = [var[self] for var in vals]
        return self.update(self.terms[index], vals, msgs, coeffs)

    def update(self, var, vals, msgs, coeffs):
        pi_inv = 0
        mu = 0
        for val, msg, coeff in itertools.izip(vals, msgs, coeffs):
            div = val / msg
            mu += coeff * div.mu
            if pi_inv == inf:
                continue
            try:
                # numpy.float64 handles floating-point error by different way.
                # For example, it can just warn RuntimeWarning on n/0 problem
                # instead of throwing ZeroDivisionError. So div.pi, the
                # denominator has to be a built-in float.
                pi_inv += coeff ** 2 / float(div.pi)
            except ZeroDivisionError:
                pi_inv = inf
        pi = 1. / pi_inv
        tau = pi * mu
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
        sqrt_pi = math.sqrt(div.pi)
        args = (div.tau / sqrt_pi, self.draw_margin * sqrt_pi)
        v = self.v_func(*args)
        w = self.w_func(*args)
        denom = (1. - w)
        pi, tau = div.pi / denom, (div.tau + sqrt_pi * v) / denom
        return val.update_value(self, pi, tau)
