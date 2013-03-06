# -*- coding: utf-8 -*-
from __future__ import with_statement

from trueskill.backends import available_backends


backends = available_backends()


def pytest_addoption(parser):
    parser.addoption('--backend', action='append', default=[])


def pytest_generate_tests(metafunc):
    if getattr(metafunc.function, '_various_backends', False):
        available = [None if str(backend).lower() == 'none' else backend
                     for backend in metafunc.config.option.backend or backends]
        selected = metafunc.function._various_backends
        if selected is True:
            parametrized_backends = available
        elif selected is False:
            parametrized_backends = None
        else:
            parametrized_backends = set(available).intersection(selected)
        metafunc.parametrize('backend', parametrized_backends)


def various_backends(backends=None):
    import inspect
    from trueskillhelpers import substituted_trueskill
    if hasattr(backends, '__call__'):
        return various_backends(True)(backends)
    def decorator(f):
        def wrapped(backend, *args, **kwargs):
            if 'backend' in inspect.getargspec(f)[0]:
                kwargs['backend'] = kwargs.get('backend', backend)
            with substituted_trueskill(backend=backend):
                return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        wrapped.__doc__ = f.__doc__
        wrapped._various_backends = backends
        return wrapped
    return decorator
