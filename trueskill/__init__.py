# -*- coding: utf-8 -*-
"""
    trueskill
    ~~~~~~~~~

    The TrueSkill rating system.

    :copyright: (c) 2012 by Heungsub Lee
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import
from itertools import chain, imap, izip
import math

from .mathematics import cdf, pdf, ppf, Gaussian, Matrix
from .factorgraph import (Variable, PriorFactor, LikelihoodFactor, SumFactor,
                          TruncateFactor)


__version__ = '0.2.1'
__all__ = ['TrueSkill', 'Rating', 'rate', 'quality', 'rate_1vs1',
           'quality_1vs1', 'setup', 'MU', 'SIGMA', 'BETA', 'TAU',
           'DRAW_PROBABILITY', 'transform_ratings', 'match_quality']


#: Default initial mean of ratings
MU = 25.
#: Default initial standard deviation of ratings
SIGMA = MU / 3
#: Default guarantee about an 80% chance of winning
BETA = SIGMA / 2
#: Default dynamic factor
TAU = SIGMA / 100
#: Default draw probability of the game
DRAW_PROBABILITY = .10
#: A basis to check reliability of the result
DELTA = 0.0001


def v_win(diff, draw_margin):
    """The non-draw version of "V" function. "V" calculates a variation of a
    mean.
    """
    x = diff - draw_margin
    return pdf(x) / cdf(x)


def v_draw(diff, draw_margin):
    """The draw version of "V" function."""
    abs_diff = abs(diff)
    a, b = draw_margin - abs_diff, -draw_margin - abs_diff
    denom = cdf(a) - cdf(b)
    numer = pdf(b) - pdf(a)
    return numer / denom * (-1 if diff < 0 else 1)


def w_win(diff, draw_margin):
    """The non-draw version of "W" function. "W" calculates a variation of a
    standard deviation.
    """
    x = diff - draw_margin
    v = v_win(diff, draw_margin)
    return v * (v + x)


def w_draw(diff, draw_margin):
    """The draw version of "W" function."""
    abs_diff = abs(diff)
    a, b = draw_margin - abs_diff, -draw_margin - abs_diff
    denom = cdf(a) - cdf(b)
    v = v_draw(abs_diff, draw_margin)
    return (v ** 2) + (a * pdf(a) - b * pdf(b)) / denom


def calc_draw_probability(draw_margin, beta, size):
    """Calculates a draw-probability from the given ``draw_margin``."""
    return 2 * cdf(draw_margin / (math.sqrt(size) * beta)) - 1


def calc_draw_margin(draw_probability, beta, size):
    """Calculates a draw-margin from the given ``draw_probability``."""
    return ppf((draw_probability + 1) / 2.) * math.sqrt(size) * beta


def _team_sizes(rating_groups):
    """Makes a size map of each teams."""
    team_sizes = [0]
    for group in rating_groups:
        team_sizes.append(len(group) + team_sizes[-1])
    del team_sizes[0]
    return team_sizes


class Rating(Gaussian):
    """Represents a player's skill as Gaussian distrubution. The default mu and
    sigma value follows the global TrueSkill environment's settings.

    :param mu: mean
    :param sigma: standard deviation
    """

    def __init__(self, mu=None, sigma=None):
        if isinstance(mu, tuple):
            mu, sigma = mu
        if mu is None:
            mu = _g().mu
        if sigma is None:
            sigma = _g().sigma
        super(Rating, self).__init__(mu, sigma)

    @property
    def exposure(self):
        """A value that will go up on the whole."""
        return self.mu - 3 * self.sigma

    def __int__(self):
        return int(self.mu)

    def __long__(self):
        return long(self.mu)

    def __float__(self):
        return float(self.mu)

    def __iter__(self):
        return iter((self.mu, self.sigma))

    def __eq__(self, other):
        return self.pi == other.pi and self.tau == other.tau

    def __lt__(self, other):
        return self.mu < other.mu

    def __le__(self, other):
        return self.mu <= other.mu

    def __gt__(self, other):
        return self.mu > other.mu

    def __ge__(self, other):
        return self.mu >= other.mu

    def __repr__(self):
        c = type(self)
        args = (c.__module__, c.__name__, self.mu, self.sigma)
        return '%s.%s(mu=%.3f, sigma=%.3f)' % args


class TrueSkill(object):
    """Implements a TrueSkill environment. An environment could have customized
    constants. Every games have not same design and may need to customize
    TrueSkill constants.

    For example, 60% of matches in your game have finished as draw then you
    should set ``draw_probability`` to 0.60::

        env = TrueSkill(draw_probability=0.60)

    For more details of the constants, see `The Math Behind TrueSkill`_.

    .. _The Math Behind TrueSkill:: http://bit.ly/trueskill-math

    :param mu: the initial mean of ratings
    :param sigma: the initial standard deviation of ratings
    :param beta: the distance that guarantees about an 80% chance of winning
    :param tau: the dynamic factor
    :param draw_probability: the draw probability of the game
    """

    def __init__(self, mu=MU, sigma=SIGMA, beta=BETA, tau=TAU,
                 draw_probability=DRAW_PROBABILITY):
        self.mu = mu
        self.sigma = sigma
        self.beta = beta
        self.tau = tau
        self.draw_probability = draw_probability

    def create_rating(self, mu=None, sigma=None):
        """Initializes new :class:`Rating` object, but it fixes default mu and
        sigma to the environment's.

        >>> env = TrueSkill(mu=0, sigma=1)
        >>> env.Rating()
        Rating(mu=0.000, sigma=1.000)
        """
        if mu is None:
            mu = self.mu
        if sigma is None:
            sigma = self.sigma
        return Rating(mu, sigma)

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
        [(Rating(...),), (Rating(...),)]
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

    def build_factor_graph(self, rating_groups, ranks, weights):
        """Makes nodes for the factor graph."""
        flatten_ratings = sum(imap(tuple, rating_groups), ())
        flatten_weights = sum(imap(tuple, weights), ())
        size = len(flatten_ratings)
        group_size = len(rating_groups)
        # create variables
        rating_vars = [Variable() for x in xrange(size)]
        perf_vars = [Variable() for x in xrange(size)]
        teamperf_vars = [Variable() for x in xrange(group_size)]
        teamdiff_vars = [Variable() for x in xrange(group_size - 1)]
        team_sizes = _team_sizes(rating_groups)
        # layer builders
        def build_rating_layer():
            for rating_var, rating in izip(rating_vars, flatten_ratings):
                yield PriorFactor(rating_var, rating, self.tau)
        def build_perf_layer():
            for rating_var, perf_var in izip(rating_vars, perf_vars):
                yield LikelihoodFactor(rating_var, perf_var, self.beta ** 2)
        def build_teamperf_layer():
            for team, teamperf_var in enumerate(teamperf_vars):
                if team > 0:
                    start = team_sizes[team - 1]
                else:
                    start = 0
                end = team_sizes[team]
                child_perf_vars = perf_vars[start:end]
                #coeffs = [1] * len(child_perf_vars)
                coeffs = flatten_weights[start:end]
                yield SumFactor(teamperf_var, child_perf_vars, coeffs)
        def build_teamdiff_layer():
            for team, teamdiff_var in enumerate(teamdiff_vars):
                yield SumFactor(teamdiff_var, teamperf_vars[team:team + 2],
                                [+1, -1])
        def build_trunc_layer():
            for x, teamdiff_var in enumerate(teamdiff_vars):
                size = sum(len(group) for group in rating_groups[x:x + 2])
                draw_margin = calc_draw_margin(self.draw_probability,
                                               self.beta, size)
                if ranks[x] == ranks[x + 1]:
                    v_func, w_func = v_draw, w_draw
                else:
                    v_func, w_func = v_win, w_win
                yield TruncateFactor(teamdiff_var, v_func, w_func, draw_margin)
        # build layers
        return (list(build_rating_layer()), list(build_perf_layer()),
                list(build_teamperf_layer()), list(build_teamdiff_layer()),
                list(build_trunc_layer()))

    def run_schedule(self, rating_layer, perf_layer, teamperf_layer,
                     teamdiff_layer, trunc_layer, min_delta=DELTA):
        """Sends messages within every nodes of the factor graph until the
        result is reliable.
        """
        if min_delta < 0:
            raise ValueError('min_delta must be greater than 0')
        # gray arrows
        for f in chain(rating_layer, perf_layer, teamperf_layer):
            f.down()
        # arrow #1, #2, #3
        teamdiff_len = len(teamdiff_layer)
        for x in xrange(10):
            if teamdiff_len == 1:
                # only two teams
                teamdiff_layer[0].down()
                delta = trunc_layer[0].up()
            else:
                # multiple teams
                delta = 0
                for x in xrange(teamdiff_len - 1):
                    teamdiff_layer[x].down()
                    delta = max(delta, trunc_layer[x].up())
                    teamdiff_layer[x].up(1)  # up to right variable
                for x in xrange(teamdiff_len - 1, 0, -1):
                    teamdiff_layer[x].down()
                    delta = max(delta, trunc_layer[x].up())
                    teamdiff_layer[x].up(0)  # up to left variable
            # repeat until to small update
            if delta <= min_delta:
                break
        # up both ends
        teamdiff_layer[0].up(0)
        teamdiff_layer[teamdiff_len - 1].up(1)
        # up the remainder of the black arrows
        for f in teamperf_layer:
            for x in xrange(len(f.vars) - 1):
                f.up(x)
        for f in perf_layer:
            f.up()

    def rate(self, rating_groups, ranks=None, weights=None, min_delta=DELTA):
        """Recalculates ratings by the ranking table::

            env = TrueSkill()
            rating_groups = [(env.create_rating(),), (env.create_rating(),)]
            rated_rating_groups = env.rate(rating_groups, ranks=[0, 1])

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
                              :class:`Rating` objects
        :param ranks: a ranking table. By default, it is same as the order of
                      the ``rating_groups``.
        :param weights: weights of each players for "partial play"
        :param min_delta: each loop checks a delta of changes and the loop
                          will stop if the delta is less then this argument
        :return: a recalculated ratings same structure as ``rating_groups``

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
        layers = self.build_factor_graph(*args)
        args = layers + (min_delta,)
        self.run_schedule(*args)
        # make result
        rating_layer, team_sizes = layers[0], _team_sizes(sorted_rating_groups)
        transformed_groups = []
        for start, end in izip([0] + team_sizes[:-1], team_sizes):
            group = []
            for f in rating_layer[start:end]:
                group.append(Rating(f.var.mu, f.var.sigma))
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
            if env.quality([team1, team2, team3]) > 0.8:
                print 'It may be a good match.'
            else:
                print 'Is not there another match?'

        :param rating_groups: a list of tuples or dictionaries containing
                              :class:`Rating` objects
        :param weights: weights of each players for "partial play"

        .. versionadded:: 0.2
        """
        rating_groups, keys = self.validate_rating_groups(rating_groups)
        weights = self.validate_weights(weights, rating_groups)
        flatten_ratings = sum(imap(tuple, rating_groups), ())
        flatten_weights = sum(imap(tuple, weights), ())
        length = len(flatten_ratings)
        # a vector of all of the skill means
        mean_matrix = Matrix([[r.mu] for r in flatten_ratings])
        # a matrix whose diagonal values are the variances (sigma^2) of each
        # of the players.
        def variance_matrix(width, height):
            for x, variance in enumerate(r.sigma ** 2
                                         for r in flatten_ratings):
                yield (x, x), variance
        variance_matrix = Matrix(variance_matrix, length, length)
        # the player-team assignment and comparison matrix
        def rotated_a_matrix(set_width, set_height):
            t = 0
            for r, (cur, next) in enumerate(izip(rating_groups[:-1],
                                                 rating_groups[1:])):
                for x in xrange(t, t + len(cur)):
                    yield (r, x), flatten_weights[x]
                    t += 1
                x += 1
                for x in xrange(x, x + len(next)):
                    yield (r, x), -flatten_weights[x]
            set_width(x + 1)
            set_height(r + 1)
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

    def rate_1vs1(self, rating1, rating2, drawn=False, min_delta=DELTA):
        """A shortcut to rate just 2 players in individual match::

            new_rating1, new_rating2 = env.rate_1vs1(rating1, rating2)

        :param rating1: the winner's rating if they didn't draw
        :param rating2: the loser's rating if they didn't draw
        :param drawn: if the players drew, set this to ``True``. Defaults to
                      ``False``.
        :param min_delta: will be passed to :meth:`rate`
        :return: recalculated 2 ratings

        .. versionadded:: 0.2
        """
        ranks = [0, 0 if drawn else 1]
        teams = self.rate([(rating1,), (rating2,)], ranks, min_delta=min_delta)
        return teams[0][0], teams[1][0]

    def quality_1vs1(self, rating1, rating2):
        """A shortcut to calculate the match quality between just 2 players in
        individual match::

            if env.quality_1vs1(rating1, rating2) > 0.8:
                print 'They look have similar skills.'
            else:
                print 'This match may be unfair!'

        .. versionadded:: 0.2
        """
        return self.quality([(rating1,), (rating2,)])

    def make_as_global(self):
        """Registers the environment as the global environment.

        >>> env = TrueSkill(mu=50)
        >>> Rating()
        Rating(mu=25.000, sigma=8.333)
        >>> env.make_as_global() #doctest: +ELLIPSIS
        <TrueSkill mu=50...>
        >>> Rating()
        Rating(mu=50.000, sigma=8.333)

        But if you need just one environment, use :func:`setup` instead.
        """
        return setup(env=self)

    def Rating(self, mu=None, sigma=None):
        """Deprecated. Used to create a :class:`Rating` object.

        .. versionchanged:: 0.2
           This method is deprecated with 0.2. Override :meth:`create_rating`
           instead.
        """
        from warnings import warn
        warn('TrueSkill.Rating is now called TrueSkill.create_rating',
             DeprecationWarning)
        return self.create_rating(mu, sigma)

    def transform_ratings(self, rating_groups, ranks=None, min_delta=DELTA):
        """Deprecated. Used to rate the given ratings.

        .. versionchanged:: 0.2
           This method is deprecated with 0.2. Override :meth:`rate` instead.
        """
        from warnings import warn
        warn('TrueSkill.transform_ratings is now called TrueSkill.rate',
             DeprecationWarning)
        rating_groups = [(r,) if isinstance(r, Rating) else r
                         for r in rating_groups]
        return self.rate(rating_groups, ranks, min_delta=min_delta)

    def match_quality(self, rating_groups):
        """Deprecated. Used to calculate a match quality.

        .. versionchanged:: 0.2
           This method is deprecated with 0.2. Override :meth:`quality`
           instead.
        """
        from warnings import warn
        warn('TrueSkill.match_quality is now called TrueSkill.quality',
             DeprecationWarning)
        rating_groups = [(r,) if isinstance(r, Rating) else r
                         for r in rating_groups]
        return self.quality(rating_groups)

    def __repr__(self):
        c = type(self)
        args = (c.__module__, c.__name__, self.mu, self.sigma, self.beta,
                self.tau, self.draw_probability * 100)
        return '<%s.%s mu=%.3f sigma=%.3f beta=%.3f tau=%.3f ' \
               'draw_probability=%.1f%%>' % args


_global = []


def _g():
    """Gets the global TrueSkill environment."""
    if not _global:
        setup()  # setup the default environment
    return _global[0]


def rate(rating_groups, ranks=None, weights=None, min_delta=DELTA):
    """A proxy function for :meth:`TrueSkill.rate` of the global TrueSkill
    environment.

    .. versionadded:: 0.2
    """
    return _g().rate(rating_groups, ranks, weights, min_delta)


def quality(rating_groups, weights=None):
    """A proxy function for :meth:`TrueSkill.quality` of the global TrueSkill
    environment.

    .. versionadded:: 0.2
    """
    return _g().quality(rating_groups, weights)


def rate_1vs1(rating1, rating2, drawn=False, min_delta=DELTA):
    """A proxy function for :meth:`TrueSkill.rate_1vs1` of the global TrueSkill
    environment.

    .. versionadded:: 0.2
    """
    return _g().rate_1vs1(rating1, rating2, drawn, min_delta)


def quality_1vs1(rating1, rating2):
    """A proxy function for :meth:`TrueSkill.quality_1vs1` of the global
    TrueSkill environment.

    .. versionadded:: 0.2
    """
    return _g().quality_1vs1(rating1, rating2)


def transform_ratings(rating_groups, ranks=None, min_delta=DELTA):
    return _g().transform_ratings(rating_groups, ranks, min_delta)


def match_quality(rating_groups):
    return _g().match_quality(rating_groups)


def setup(mu=MU, sigma=SIGMA, beta=BETA, tau=TAU,
          draw_probability=DRAW_PROBABILITY, env=None):
    """Setups the global TrueSkill environment.

    >>> Rating()
    Rating(mu=25.000, sigma=8.333)
    >>> setup(mu=50) #doctest: +ELLIPSIS
    <TrueSkill mu=50...>
    >>> Rating()
    Rating(mu=50.000, sigma=8.333)
    """
    try:
        _global.pop()
    except IndexError:
        pass
    _global.append(env or TrueSkill(mu, sigma, beta, tau, draw_probability))
    return _g()
