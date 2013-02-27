# -*- coding: utf-8 -*-
from contextlib import contextmanager
import logging


@contextmanager
def factorgraph_logging():
    import trueskill.factorgraph as f
    logger = logging.getLogger('TrueSkill')
    def _patch(Factor):
        Factor._up, Factor._down = Factor.up, Factor.down
        def up(self, *args, **kwargs):
            rv = self._up(*args, **kwargs)
            logger.debug('{0} up {1:.3f}'.format(Factor.__name__, rv))
            return rv
        def down(self, *args, **kwargs):
            rv = self._down(*args, **kwargs)
            logger.debug('{0} down {1:.3f}'.format(Factor.__name__, rv))
            return rv
        Factor.up, Factor.down = up, down
    def _unpatch(Factor):
        Factor.up, Factor.down = Factor._up, Factor._down
        del Factor._up, Factor._down
    factor_names = ['PriorFactor', 'LikelihoodFactor', 'SumFactor',
                    'TruncateFactor']
    for factor_name in factor_names:
        _patch(getattr(f, factor_name))
    yield logger
    for factor_name in factor_names:
        _unpatch(getattr(f, factor_name))


@contextmanager
def force_scipycompat():
    """Don't use scipy within a context."""
    import trueskill as t
    import trueskill.scipycompat as c
    cdf, pdf, ppf = t.cdf, t.pdf, t.ppf
    t.cdf, t.pdf, t.ppf = c.cdf, c.pdf, c.ppf
    yield
    t.cdf, t.pdf, t.ppf = cdf, pdf, ppf
