# -*- coding: utf-8 -*-
from __future__ import with_statement
from contextlib import contextmanager
import functools
import inspect
import logging

import trueskill
from trueskill.factorgraph import Factor, Variable
from trueskill.mathematics import Gaussian
from trueskill.statistics import available_implements


@contextmanager
def factorgraph_logging(color=False):
    """In the context, a factorgraph prints logs as DEBUG level. It will help
    to follow factograph running schedule.

    ::

        with factograph_logging() as logger:
            logger.setLevel(DEBUG)
            logger.addHandler(StreamHandler(sys.stderr))
            rate_1vs1(Rating(), Rating())
    """
    import inspect
    # color mode uses the termcolor module
    if color:
        try:
            from termcolor import colored
        except ImportError:
            raise ImportError('To enable color mode, install termcolor')
    else:
        colored = lambda s, *a, **k: s
    logger = logging.getLogger('TrueSkill')
    orig_factor_init = Factor.__init__
    orig_variable_set = Variable.set
    def repr_factor(factor):
        return '{0}@{1}'.format(type(factor).__name__, id(factor))
    def repr_gauss(gauss):
        return 'N(mu=%.3f, sigma=%.3f, pi=%r, tau=%r)' % \
               (gauss.mu, gauss.sigma, gauss.pi, gauss.tau)
    def r(val):
        if isinstance(val, Factor):
            return repr_factor(val)
        elif isinstance(val, Gaussian):
            return repr_gauss(val)
        else:
            return repr(val)
    def factor_init(self, *args, **kwargs):
        frames = inspect.getouterframes(inspect.currentframe())
        layer_builder_name = frames[2][3]
        assert (layer_builder_name.startswith('build_') and
                layer_builder_name.endswith('_layer'))
        self._layer_name = layer_builder_name[6:].replace('_', ' ').title()
        return orig_factor_init(self, *args, **kwargs)
    def variable_set(self, val):
        old_value = Gaussian(pi=self.pi, tau=self.tau)
        old_messages = dict((fac, Gaussian(pi=msg.pi, tau=msg.tau))
                            for fac, msg in self.messages.iteritems())
        delta = orig_variable_set(self, val)
        # inspect outer frames
        frames = inspect.getouterframes(inspect.currentframe())
        methods = [None, None]
        for frame in frames:
            method = frame[3]
            if method.startswith('update_'):
                methods[0] = method
            elif method in ('up', 'down'):
                methods[1] = method
                break
        if methods[1] == 'down':
            return delta
        factor = frame[0].f_locals['self']
        before = Gaussian(pi=self.pi, tau=self.tau)
        # helpers for logging
        logs = []
        l = logs.append
        bullet = lambda changed: colored(' * ', 'red') if changed else '   '
        # print layer
        if getattr(logger, '_prev_layer_name', None) != factor._layer_name:
            logger._prev_layer_name = factor._layer_name
            l(colored('[{0}]'.format(factor._layer_name), 'blue'))
        # print factor
        l(colored('<{0}.{1}>'.format(r(factor), methods[1]), 'cyan'))
        # print value
        if old_value == self:
            line = '{0}'.format(r(self))
        else:
            line = '{0} -> {1}'.format(r(old_value), r(self))
        l(bullet(methods[0] == 'update_value') + line)
        # print messages
        fmt = '{0}: {1} -> {2}'.format
        for fac, msg in self.messages.iteritems():
            old_msg = old_messages[fac]
            changed = fac is factor and methods[0] == 'update_message'
            if old_msg == msg:
                line = '{0}: {1}'.format(r(fac), r(msg))
            else:
                line = '{0}: {1} -> {2}'.format(r(fac), r(old_msg), r(msg))
            l(bullet(changed) + line)
        # print buffered logs
        map(logger.debug, logs)
        return delta
    Factor.__init__, Variable.set = factor_init, variable_set
    yield logger
    Factor.__init__, Variable.set = orig_factor_init, orig_variable_set


@contextmanager
def similar_env(env=None, **kwargs):
    if env is None:
        env = trueskill._g()
    env_kwargs = {'mu': env.mu, 'sigma': env.sigma, 'beta': env.beta,
                  'tau': env.tau, 'draw_probability': env.draw_probability,
                  'stats_implement': env.stats_implement}
    env_kwargs.update(kwargs)
    yield trueskill.setup(**env_kwargs)
    trueskill.setup(env=env)


def all_stats_implements(f=None):
    if f is None:
        def iterate():
            for name in available_implements():
                with similar_env(stats_implement=name) as env:
                    yield env
        return iterate()
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        for stats_implement in all_stats_implements():
            if 'stats_implement' in inspect.getargspec(f)[0]:
                kwargs['stats_implement'] = stats_implement
            f(*args, **kwargs)
    return wrapped
