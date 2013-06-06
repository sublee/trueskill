# -*- coding: utf-8 -*-
"""
    trueskill
    ~~~~~~~~~

    The video game rating system.

    :copyright: (c) 2012-2013 by Heungsub Lee
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import
from itertools import chain, imap, izip
import math

from .backends import choose_backend
from .factorgraph import (Variable, PriorFactor, LikelihoodFactor, SumFactor,
                          TruncateFactor)
from .mathematics import Gaussian, Matrix


__version__ = '0.4.1'
__all__ = [
    # TrueSkill objects
    'TrueSkill', 'Rating',
    # functions for the global environment
    'rate', 'quality', 'rate_1vs1', 'quality_1vs1', 'expose', 'setup',
    'global_env',
    # default values
    'MU', 'SIGMA', 'BETA', 'TAU', 'DRAW_PROBABILITY',
    # draw probability helpers
    'calc_draw_probability', 'calc_draw_margin',
    # deprecated features
    'transform_ratings', 'match_quality', 'dynamic_draw_probability',
]


#: Default initial mean of ratings.
MU = 25.
#: Default initial standard deviation of ratings.
SIGMA = MU / 3
#: Default distance that guarantees about 75.6% chance of winning.
BETA = SIGMA / 2
#: Default dynamic factor.
TAU = SIGMA / 100
#: Default draw probability of the game.
DRAW_PROBABILITY = .10
#: A basis to check reliability of the result.
DELTA = 0.0001


def calc_draw_probability(draw_margin, size, env=None):
    """Calculates a draw-probability from the given ``draw_margin``.

    :param draw_margin: the draw-margin.
    :param size: the number of players in two comparing teams.
    :param env: the :class:`TrueSkill` object. Defaults to the global
                environment.
    """
    if env is None:
        env = global_env()
    return 2 * env.cdf(draw_margin / (math.sqrt(size) * env.beta)) - 1


def calc_draw_margin(draw_probability, size, env=None):
    """Calculates a draw-margin from the given ``draw_probability``.

    :param draw_probability: the draw-probability.
    :param size: the number of players in two comparing teams.
    :param env: the :class:`TrueSkill` object. Defaults to the global
                environment.
    """
    if env is None:
        env = global_env()
    return env.ppf((draw_probability + 1) / 2.) * math.sqrt(size) * env.beta


def _team_sizes(rating_groups):
    """Makes a size map of each teams."""
    team_sizes = [0]
    for group in rating_groups:
        team_sizes.append(len(group) + team_sizes[-1])
    del team_sizes[0]
    return team_sizes


def _floating_point_error(env):
    if env.backend == 'mpmath':
        msg = 'Set "mpmath.mp.dps" to higher'
    else:
        msg = 'Cannot calculate correctly, set backend to "mpmath"'
    return FloatingPointError(msg)


class Rating(Gaussian):
    """Represents a player's skill as Gaussian distrubution.

    The default mu and sigma value follows the global environment's settings.
    If you don't want to use the global, use :meth:`TrueSkill.create_rating` to
    create the rating object.

    :param mu: the mean.
    :param sigma: the standard deviation.
    """

    def __init__(self, mu=None, sigma=None):
        if isinstance(mu, tuple):
            mu, sigma = mu
        elif isinstance(mu, Gaussian):
            mu, sigma = mu.mu, mu.sigma
        if mu is None:
            mu = global_env().mu
        if sigma is None:
            sigma = global_env().sigma
        super(Rating, self).__init__(mu, sigma)

    def __int__(self):
        return int(self.mu)

    def __long__(self):
        return long(self.mu)

    def __float__(self):
        return float(self.mu)

    def __iter__(self):
        return iter((self.mu, self.sigma))

    def __repr__(self):
        c = type(self)
        args = ('.'.join([c.__module__, c.__name__]), self.mu, self.sigma)
        return '%s(mu=%.3f, sigma=%.3f)' % args


class TrueSkill(object):
    """Implements a TrueSkill environment. An environment could have customized
    constants. Every games have not same design and may need to customize
    TrueSkill constants.

    For example, 60% of matches in your game have finished as draw then you
    should set ``draw_probability`` to 0.60::

       env = TrueSkill(draw_probability=0.60)

    For more details of the constants, see `The Math Behind TrueSkill`_ by
    Jeff Moser.

    .. _The Math Behind TrueSkill:: http://bit.ly/trueskill-math

    :param mu: the initial mean of ratings.
    :param sigma: the initial standard deviation of ratings. The recommended
                  value is a third of ``mu``.
    :param beta: the distance which guarantees about 75.6% chance of winning.
                 The recommended value is a half of ``sigma``.
    :param tau: the dynamic factor which restrains a fixation of rating. The
                recommended value is ``sigma`` per cent.
    :param draw_probability: the draw probability between two teams. It can be
                             a ``float`` or function which returns a ``float``
                             by the given two rating (team performance)
                             arguments and the beta value. If it is a
                             ``float``, the game has fixed draw probability.
                             Otherwise, the draw probability will be decided
                             dynamically per each match.
    :param backend: the name of a backend which implements cdf, pdf, ppf. See
                    :mod:`trueskill.backends` for more details. Defaults to
                    ``None``.
    """

    def __init__(self, mu=MU, sigma=SIGMA, beta=BETA, tau=TAU,
                 draw_probability=DRAW_PROBABILITY, backend=None):
        self.mu = mu
        self.sigma = sigma
        self.beta = beta
        self.tau = tau
        self.draw_probability = draw_probability
        self.backend = backend
        if isinstance(backend, tuple):
            self.cdf, self.pdf, self.ppf = backend
        else:
            self.cdf, self.pdf, self.ppf = choose_backend(backend)

    def create_rating(self, mu=None, sigma=None):
        """Initializes new :class:`Rating` object, but it fixes default mu and
        sigma to the environment's.

        >>> env = TrueSkill(mu=0, sigma=1)
        >>> env.Rating()
        trueskill.Rating(mu=0.000, sigma=1.000)
        """
        if mu is None:
            mu = self.mu
        if sigma is None:
            sigma = self.sigma
        return Rating(mu, sigma)

    def v_win(self, diff, draw_margin):
        """The non-draw version of "V" function. "V" calculates a variation of
        a mean.
        """
        x = diff - draw_margin
        denom = self.cdf(x)
        return (self.pdf(x) / denom) if denom else -x

    def v_draw(self, diff, draw_margin):
        """The draw version of "V" function."""
        abs_diff = abs(diff)
        a, b = draw_margin - abs_diff, -draw_margin - abs_diff
        denom = self.cdf(a) - self.cdf(b)
        numer = self.pdf(b) - self.pdf(a)
        return ((numer / denom) if denom else a) * (-1 if diff < 0 else +1)

    def w_win(self, diff, draw_margin):
        """The non-draw version of "W" function. "W" calculates a variation of
        a standard deviation.
        """
        x = diff - draw_margin
        v = self.v_win(diff, draw_margin)
        w = v * (v + x)
        if 0 < w < 1:
            return w
        raise _floating_point_error(self)

    def w_draw(self, diff, draw_margin):
        """The draw version of "W" function."""
        abs_diff = abs(diff)
        a, b = draw_margin - abs_diff, -draw_margin - abs_diff
        denom = self.cdf(a) - self.cdf(b)
        if not denom:
            raise _floating_point_error(self)
        v = self.v_draw(abs_diff, draw_margin)
        return (v ** 2) + (a * self.pdf(a) - b * self.pdf(b)) / denom

    def validate_rating_groups(self, rating_groups):
        """Validates a ``rating_groups`` argument. It should contain more than
        2 groups and all groups must not be empty.

        >>> env = TrueSkill()
        >>> env.validate_rating_groups([])
        Traceback (most recent call last):
            ...
        ValueError: need multiple rating groups
        >>> env.validate_rating_groups([(Rating(),)])
        Traceback (most recent call last):
            ...
        ValueError: need multiple rating groups
        >>> env.validate_rating_groups([(Rating(),), ()])
        Traceback (most recent call last):
            ...
        ValueError: each group must contain multiple ratings
        >>> env.validate_rating_groups([(Rating(),), (Rating(),)])
        ... #doctest: +ELLIPSIS
        [(truekill.Rating(...),), (trueskill.Rating(...),)]
        """
        # check group sizes
        if len(rating_groups) < 2:
            raise ValueError('Need multiple rating groups')
        elif not all(rating_groups):
            raise ValueError('Each group must contain multiple ratings')
        # check group types
        group_types = set(imap(type, rating_groups))
        if len(group_types) != 1:
            raise TypeError('All groups should be same type')
        elif group_types.pop() is Rating:
            raise TypeError('Rating cannot be a rating group')
        # normalize rating_groups
        if isinstance(rating_groups[0], dict):
            keys = map(dict.keys, rating_groups)
            rating_groups = (tuple(g.itervalues()) for g in rating_groups)
        else:
            keys = None
        return list(rating_groups), keys

    def validate_weights(self, weights, rating_groups):
        if weights is None:
            weights = [(1,) * len(g) for g in rating_groups]
        elif isinstance(weights, dict):
            weights_dict, weights = weights, []
            for x, group in enumerate(rating_groups):
                w = []
                weights.append(w)
                for y, rating in enumerate(group):
                    w.append(weights_dict.get((x, y), 1))
        return weights

    def factor_graph_builders(self, rating_groups, ranks, weights):
        """Makes nodes for the TrueSkill factor graph.

        Here's an example of a TrueSkill factor graph when 1 vs 2 vs 1 match::

             rating_layer:  O O O O  (PriorFactor)
                            | | | |
                            | | | |
               perf_layer:  O O O O  (LikelihoodFactor)
                            | \ / |
                            |  |  |
           team_perf_layer:  O  O  O  (SumFactor)
                            \ / \ /
                             |   |
           team_diff_layer:   O   O   (SumFactor)
                             |   |
                             |   |
              trunc_layer:   O   O   (TruncateFactor)
        """
        flatten_ratings = sum(imap(tuple, rating_groups), ())
        flatten_weights = sum(imap(tuple, weights), ())
        size = len(flatten_ratings)
        group_size = len(rating_groups)
        # create variables
        rating_vars = [Variable() for x in xrange(size)]
        perf_vars = [Variable() for x in xrange(size)]
        team_perf_vars = [Variable() for x in xrange(group_size)]
        team_diff_vars = [Variable() for x in xrange(group_size - 1)]
        team_sizes = _team_sizes(rating_groups)
        # layer builders
        def build_rating_layer():
            for rating_var, rating in izip(rating_vars, flatten_ratings):
                yield PriorFactor(rating_var, rating, self.tau)
        def build_perf_layer():
            for rating_var, perf_var in izip(rating_vars, perf_vars):
                yield LikelihoodFactor(rating_var, perf_var, self.beta ** 2)
        def build_team_perf_layer():
            for team, team_perf_var in enumerate(team_perf_vars):
                if team > 0:
                    start = team_sizes[team - 1]
                else:
                    start = 0
                end = team_sizes[team]
                child_perf_vars = perf_vars[start:end]
                coeffs = flatten_weights[start:end]
                yield SumFactor(team_perf_var, child_perf_vars, coeffs)
        def build_team_diff_layer():
            for team, team_diff_var in enumerate(team_diff_vars):
                yield SumFactor(team_diff_var,
                                team_perf_vars[team:team + 2], [+1, -1])
        def build_trunc_layer():
            for x, team_diff_var in enumerate(team_diff_vars):
                if callable(self.draw_probability):
                    # dynamic draw probability
                    team_perf1, team_perf2 = team_perf_vars[x:x + 2]
                    args = (Rating(team_perf1), Rating(team_perf2), self)
                    draw_probability = self.draw_probability(*args)
                else:
                    # static draw probability
                    draw_probability = self.draw_probability
                size = sum(map(len, rating_groups[x:x + 2]))
                draw_margin = calc_draw_margin(draw_probability, size, self)
                if ranks[x] == ranks[x + 1]:  # is a tie?
                    v_func, w_func = self.v_draw, self.w_draw
                else:
                    v_func, w_func = self.v_win, self.w_win
                yield TruncateFactor(team_diff_var,
                                     v_func, w_func, draw_margin)
        # build layers
        return (build_rating_layer, build_perf_layer, build_team_perf_layer,
                build_team_diff_layer, build_trunc_layer)

    def run_schedule(self, build_rating_layer, build_perf_layer,
                     build_team_perf_layer, build_team_diff_layer,
                     build_trunc_layer, min_delta=DELTA):
        """Sends messages within every nodes of the factor graph until the
        result is reliable.
        """
        if min_delta <= 0:
            raise ValueError('min_delta must be greater than 0')
        layers = []
        def build(builders):
            layers_built = [list(build()) for build in builders]
            layers.extend(layers_built)
            return layers_built
        # gray arrows
        layers_built = build([build_rating_layer,
                              build_perf_layer,
                              build_team_perf_layer])
        rating_layer, perf_layer, team_perf_layer = layers_built
        for f in chain(*layers_built):
            f.down()
        # arrow #1, #2, #3
        team_diff_layer, trunc_layer = build([build_team_diff_layer,
                                              build_trunc_layer])
        team_diff_len = len(team_diff_layer)
        for x in xrange(10):
            if team_diff_len == 1:
                # only two teams
                team_diff_layer[0].down()
                delta = trunc_layer[0].up()
            else:
                # multiple teams
                delta = 0
                for x in xrange(team_diff_len - 1):
                    team_diff_layer[x].down()
                    delta = max(delta, trunc_layer[x].up())
                    team_diff_layer[x].up(1)  # up to right variable
                for x in xrange(team_diff_len - 1, 0, -1):
                    team_diff_layer[x].down()
                    delta = max(delta, trunc_layer[x].up())
                    team_diff_layer[x].up(0)  # up to left variable
            # repeat until to small update
            if delta <= min_delta:
                break
        # up both ends
        team_diff_layer[0].up(0)
        team_diff_layer[team_diff_len - 1].up(1)
        # up the remainder of the black arrows
        for f in team_perf_layer:
            for x in xrange(len(f.vars) - 1):
                f.up(x)
        for f in perf_layer:
            f.up()
        return layers

    def rate(self, rating_groups, ranks=None, weights=None, min_delta=DELTA):
        """Recalculates ratings by the ranking table::

           env = TrueSkill()  # uses default settings
           # create ratings
           r1 = env.create_rating(42.222)
           r2 = env.create_rating(89.999)
           # calculate new ratings
           rating_groups = [(r1,), (r2,)]
           rated_rating_groups = env.rate(rating_groups, ranks=[0, 1])
           # save new ratings
           (r1,), (r2,) = rated_rating_groups

        ``rating_groups`` is a list of rating tuples or dictionaries that
        represents each team of the match. You will get a result as same
        structure as this argument. Rating dictionaries for this may be useful
        to choose specific player's new rating::

           # load players from the database
           p1 = load_player_from_database('Arpad Emrick Elo')
           p2 = load_player_from_database('Mark Glickman')
           p3 = load_player_from_database('Heungsub Lee')
           # calculate new ratings
           rating_groups = [{p1: p1.rating, p2: p2.rating}, {p3: p3.rating}]
           rated_rating_groups = env.rate(rating_groups, ranks=[0, 1])
           # save new ratings
           for player in [p1, p2, p3]:
               player.rating = rated_rating_groups[player.team][player]

        :param rating_groups: a list of tuples or dictionaries containing
                              :class:`Rating` objects.
        :param ranks: a ranking table. By default, it is same as the order of
                      the ``rating_groups``.
        :param weights: weights of each players for "partial play".
        :param min_delta: each loop checks a delta of changes and the loop
                          will stop if the delta is less then this argument.
        :returns: recalculated ratings same structure as ``rating_groups``.
        :raises: :exc:`FloatingPointError` occurs when winners have too lower
                 rating than losers. higher floating-point precision couls
                 solve this error. set the backend to "mpmath".

        .. versionadded:: 0.2
        """
        rating_groups, keys = self.validate_rating_groups(rating_groups)
        weights = self.validate_weights(weights, rating_groups)
        group_size = len(rating_groups)
        if ranks is None:
            ranks = range(group_size)
        elif len(ranks) != group_size:
            raise ValueError('Wrong ranks')
        # sort rating groups by rank
        by_rank = lambda x: x[1][1]
        sorting = sorted(enumerate(izip(rating_groups, ranks, weights)),
                         key=by_rank)
        sorted_rating_groups, sorted_ranks, sorted_weights = [], [], []
        for x, (g, r, w) in sorting:
            sorted_rating_groups.append(g)
            sorted_ranks.append(r)
            # make weights to be greater than 0
            sorted_weights.append(max(min_delta, w_) for w_ in w)
        # build factor graph
        args = (sorted_rating_groups, sorted_ranks, sorted_weights)
        builders = self.factor_graph_builders(*args)
        args = builders + (min_delta,)
        layers = self.run_schedule(*args)
        # make result
        rating_layer, team_sizes = layers[0], _team_sizes(sorted_rating_groups)
        transformed_groups = []
        for start, end in izip([0] + team_sizes[:-1], team_sizes):
            group = []
            for f in rating_layer[start:end]:
                group.append(Rating(float(f.var.mu), float(f.var.sigma)))
            transformed_groups.append(tuple(group))
        by_hint = lambda x: x[0]
        unsorting = sorted(izip((x for x, __ in sorting), transformed_groups),
                           key=by_hint)
        if keys is None:
            return [g for x, g in unsorting]
        # restore the structure with input dictionary keys
        return [dict(izip(keys[x], g)) for x, g in unsorting]

    def quality(self, rating_groups, weights=None):
        """Calculates the match quality of the given rating groups. A result
        is the draw probability in the association::

          env = TrueSkill()
          if env.quality([team1, team2, team3]) < 0.50:
              print('This match seems to be not so fair')

        :param rating_groups: a list of tuples or dictionaries containing
                              :class:`Rating` objects.
        :param weights: weights of each players for "partial play".

        .. versionadded:: 0.2
        """
        rating_groups, keys = self.validate_rating_groups(rating_groups)
        weights = self.validate_weights(weights, rating_groups)
        flatten_ratings = sum(imap(tuple, rating_groups), ())
        flatten_weights = sum(imap(tuple, weights), ())
        length = len(flatten_ratings)
        # a vector of all of the skill means
        mean_matrix = Matrix([[r.mu] for r in flatten_ratings])
        # a matrix whose diagonal values are the variances (sigma ** 2) of each
        # of the players.
        def variance_matrix(height, width):
            variances = (r.sigma ** 2 for r in flatten_ratings)
            for x, variance in enumerate(variances):
                yield (x, x), variance
        variance_matrix = Matrix(variance_matrix, length, length)
        # the player-team assignment and comparison matrix
        def rotated_a_matrix(set_height, set_width):
            t = 0
            for r, (cur, next) in enumerate(izip(rating_groups[:-1],
                                                 rating_groups[1:])):
                for x in xrange(t, t + len(cur)):
                    yield (r, x), flatten_weights[x]
                    t += 1
                x += 1
                for x in xrange(x, x + len(next)):
                    yield (r, x), -flatten_weights[x]
            set_height(r + 1)
            set_width(x + 1)
        rotated_a_matrix = Matrix(rotated_a_matrix)
        a_matrix = rotated_a_matrix.transpose()
        # match quality further derivation
        _ata = (self.beta ** 2) * rotated_a_matrix * a_matrix
        _atsa = rotated_a_matrix * variance_matrix * a_matrix
        start = mean_matrix.transpose() * a_matrix
        middle = _ata + _atsa
        end = rotated_a_matrix * mean_matrix
        # make result
        e_arg = (-0.5 * start * middle.inverse() * end).determinant()
        s_arg = _ata.determinant() / middle.determinant()
        return math.exp(e_arg) * math.sqrt(s_arg)

    def expose(self, rating):
        """Returns the value of the rating exposure. It starts from 0 and
        converges to the mean. Use this as a sort key in a leaderboard::

           leaderboard = sorted(ratings, key=env.expose, reverse=True)

        .. versionadded:: 0.4
        """
        k = self.mu / self.sigma
        return rating.mu - k * rating.sigma

    def make_as_global(self):
        """Registers the environment as the global environment.

        >>> env = TrueSkill(mu=50)
        >>> Rating()
        trueskill.Rating(mu=25.000, sigma=8.333)
        >>> env.make_as_global()  #doctest: +ELLIPSIS
        trueskill.TrueSkill(mu=50.000, ...)
        >>> Rating()
        trueskill.Rating(mu=50.000, sigma=8.333)

        But if you need just one environment, :func:`setup` is better to use.
        """
        return setup(env=self)

    def __repr__(self):
        c = type(self)
        if callable(self.draw_probability):
            f = self.draw_probability
            draw_probability = '.'.join([f.__module__, f.__name__])
        else:
            draw_probability = '%.1f%%' % (self.draw_probability * 100)
        if self.backend is None:
            backend = ''
        elif isinstance(self.backend, tuple):
            backend = ', backend=...'
        else:
            backend = ', backend=%r' % self.backend
        args = ('.'.join([c.__module__, c.__name__]), self.mu, self.sigma,
                self.beta, self.tau, draw_probability, backend)
        return ('%s(mu=%.3f, sigma=%.3f, beta=%.3f, tau=%.3f, '
                'draw_probability=%s%s)' % args)


def rate_1vs1(rating1, rating2, drawn=False, min_delta=DELTA, env=None):
    """A shortcut to rate just 2 players in a head-to-head match::

       alice, bob = Rating(25), Rating(30)
       alice, bob = rate_1vs1(alice, bob)
       alice, bob = rate_1vs1(alice, bob, drawn=True)

    :param rating1: the winner's rating if they didn't draw.
    :param rating2: the loser's rating if they didn't draw.
    :param drawn: if the players drew, set this to ``True``. Defaults to
                  ``False``.
    :param min_delta: will be passed to :meth:`rate`.
    :param env: the :class:`TrueSkill` object. Defaults to the global
                environment.
    :returns: a tuple containing recalculated 2 ratings.

    .. versionadded:: 0.2
    """
    if env is None:
        env = global_env()
    ranks = [0, 0 if drawn else 1]
    teams = env.rate([(rating1,), (rating2,)], ranks, min_delta=min_delta)
    return teams[0][0], teams[1][0]


def quality_1vs1(rating1, rating2, env=None):
    """A shortcut to calculate the match quality between just 2 players in
    a head-to-head match::

       if quality_1vs1(alice, bob) < 0.50:
           print('This match seems to be not so fair')

    :param rating1: the rating.
    :param rating2: the another rating.
    :param env: the :class:`TrueSkill` object. Defaults to the global
                environment.

    .. versionadded:: 0.2
    """
    if env is None:
        env = global_env()
    return env.quality([(rating1,), (rating2,)])


def global_env():
    """Gets the :class:`TrueSkill` object which is the global environment."""
    try:
        global_env.__trueskill__
    except AttributeError:
        # setup the default environment
        setup()
    return global_env.__trueskill__


def setup(mu=MU, sigma=SIGMA, beta=BETA, tau=TAU,
          draw_probability=DRAW_PROBABILITY, backend=None, env=None):
    """Setups the global environment.

    :param env: the specific :class:`TrueSkill` object to be the global
                environment. It is optional.

    >>> Rating()
    trueskill.Rating(mu=25.000, sigma=8.333)
    >>> setup(mu=50)  #doctest: +ELLIPSIS
    trueskill.TrueSkill(mu=50.000, ...)
    >>> Rating()
    trueskill.Rating(mu=50.000, sigma=8.333)
    """
    if env is None:
        env = TrueSkill(mu, sigma, beta, tau, draw_probability, backend)
    global_env.__trueskill__ = env
    return env


def rate(rating_groups, ranks=None, weights=None, min_delta=DELTA):
    """A proxy function for :meth:`TrueSkill.rate` of the global environment.

    .. versionadded:: 0.2
    """
    return global_env().rate(rating_groups, ranks, weights, min_delta)


def quality(rating_groups, weights=None):
    """A proxy function for :meth:`TrueSkill.quality` of the global
    environment.

    .. versionadded:: 0.2
    """
    return global_env().quality(rating_groups, weights)


def expose(rating):
    """A proxy function for :meth:`TrueSkill.expose` of the global environment.

    .. versionadded:: 0.4
    """
    return global_env().expose(rating)


# append deprecated methods into :class:`TrueSkill` and :class:`Rating`
from . import deprecated
from .deprecated import (transform_ratings, match_quality,
                         dynamic_draw_probability)
deprecated.ensure_backward_compatibility(TrueSkill, Rating)
