# -*- coding: utf-8 -*-
from contextlib import contextmanager
import logging


@contextmanager
def factorgraph_logging():
    import inspect
    from trueskill.factorgraph import Variable
    from trueskill.mathematics import Gaussian
    logger = logging.getLogger('TrueSkill')
    orig_set = Variable.set
    def set(self, val):
        frames = inspect.getouterframes(inspect.currentframe())
        for frame in frames:
            method = frame[3]
            if method in ('up', 'down'):
                break
        factor = type(frame[0].f_locals['self']).__name__
        before = Gaussian(pi=self.pi, tau=self.tau)
        logger.debug('{0}.{1}: {3}'.format(factor, method, before, val))
        return orig_set(self, val)
    Variable.set = set
    yield logger
    Variable.set = orig_set


@contextmanager
def force_scipycompat():
    """Don't use scipy within a context."""
    import trueskill as t
    import trueskill.scipycompat as c
    cdf, pdf, ppf = t.cdf, t.pdf, t.ppf
    t.cdf, t.pdf, t.ppf = c.cdf, c.pdf, c.ppf
    yield
    t.cdf, t.pdf, t.ppf = cdf, pdf, ppf
