from __future__ import absolute_import

import math

from .mathematics import cdf, pdf, ppf, Gaussian


MU = 25. # initial mean
SIGMA = MU / 3 # initial standard deviation
BETA = SIGMA / 2 # guarantee about an 80% chance of winning
TAU = SIGMA / 100 # dynamic factor
DRAW_PROBABILITY = .10 # draw probability of the game


def V(diff, draw_margin):
    """The non-draw version of "V" function. "V" calculates a variation of a
    mean.
    """
    x = diff - draw_margin
    return pdf(x) / cdf(x)


def W(diff, draw_margin):
    """The non-draw version of "W" function. "W" calculates a variation of a
    standard deviation.
    """
    x = diff - draw_margin
    v = V(diff, draw_margin)
    return v * (v + x)


def V_draw(diff, draw_margin):
    """The draw version of "V" function."""
    abs_diff = abs(diff)
    a, b = draw_margin - abs_diff, -draw_margin - abs_diff
    denom = cdf(a) - cdf(b)
    numer = pdf(b) - pdf(a)
    return numer / denom * (-1 if diff < 0 else 1)


def W_draw(diff, draw_margin):
    """The draw version of "W" function."""
    abs_diff = abs(diff)
    a, b = draw_margin - abs_diff, -draw_margin - abs_diff
    denom = cdf(a) - cdf(b)
    v = V_draw(abs_diff, draw_margin)
    return (v ** 2) + (a * pdf(a) - b * pdf(b)) / denom


def calc_draw_probability(draw_margin, beta, size):
    return 2 * cdf(draw_margin / (math.sqrt(size) * beta)) - 1


def calc_draw_margin(draw_probability, beta, size):
    return ppf((draw_probability + 1) / 2.) * math.sqrt(size) * beta


def _team_sizes(rating_groups):
    team_sizes = [0]
    for group in rating_groups:
        team_sizes.append(len(group) + team_sizes[-1])
    del team_sizes[0]
    return team_sizes


class Rating(Gaussian):

    def __init__(self, mu=MU, sigma=SIGMA):
        if isinstance(mu, tuple):
            mu, sigma = mu
        super(Rating, self).__init__(mu, sigma)

    @property
    def exposure(self):
        return self.mu - 3 * self.sigma

    def __iter__(self):
        return iter((self.mu, self.sigma))

    def __repr__(self):
        args = (type(self).__name__, self.mu, self.sigma, self.exposure)
        return '%s(mu=%.3f, sigma=%.3f, exposure=%.1f)' % args


class TrueSkill(object):

    def __init__(self, mu=MU, sigma=SIGMA, beta=BETA, tau=TAU,
                 draw_probability=DRAW_PROBABILITY):
        self.mu = mu
        self.sigma = sigma
        self.beta = beta
        self.tau = tau
        self.draw_probability = draw_probability

    def build_factor_graph(self, rating_groups, ranks):
        from .factorgraph import Variable, PriorFactor, LikelihoodFactor, \
                                 SumFactor, TruncateFactor
        ratings = sum(rating_groups, ())
        size = len(ratings)
        group_size = len(rating_groups)
        # create variables
        rating_vars = [Variable() for x in xrange(size)]
        perf_vars = [Variable() for x in xrange(size)]
        teamperf_vars = [Variable() for x in xrange(group_size)]
        teamdiff_vars = [Variable() for x in xrange(group_size - 1)]
        team_sizes = _team_sizes(rating_groups)
        def get_perf_vars_by_team(team):
            if team > 0:
                start = team_sizes[team - 1]
            else:
                start = 0
            end = team_sizes[team]
            return perf_vars[start:end]
        # layer builders
        def build_rating_layer():
            for rating_var, rating in zip(rating_vars, ratings):
                yield PriorFactor(rating_var, rating, self.tau)
        def build_perf_layer():
            for rating_var, perf_var in zip(rating_vars, perf_vars):
                yield LikelihoodFactor(rating_var, perf_var, self.beta ** 2)
        def build_teamperf_layer():
            for team, teamperf_var in enumerate(teamperf_vars):
                child_perf_vars = get_perf_vars_by_team(team)
                yield SumFactor(teamperf_var, child_perf_vars,
                                [1] * len(child_perf_vars))
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
                    v_func, w_func = V_draw, W_draw
                else:
                    v_func, w_func = V, W
                yield TruncateFactor(teamdiff_var, v_func, w_func, draw_margin)
        # build layers
        return list(build_rating_layer()), \
               list(build_perf_layer()), \
               list(build_teamperf_layer()), \
               list(build_teamdiff_layer()), \
               list(build_trunc_layer())


    def run_schedule(self, rating_layer, perf_layer, teamperf_layer,
                     teamdiff_layer, trunc_layer):
        # gray arrows
        for f in rating_layer + perf_layer + teamperf_layer:
            f.down()
        # arrow #1, #2, #3
        teamdiff_len = len(teamdiff_layer)
        while True:
            if teamdiff_len == 1:
                # only two teams
                teamdiff_layer[0].down()
                delta = trunc_layer[0].up()
            else:
                # multiple teams
                for x in xrange(teamdiff_len - 1):
                    teamdiff_layer[x].down()
                    delta = trunc_layer[x].up()
                    teamdiff_layer[x].up(1) # up to right variable
                for x in xrange(teamdiff_len - 1, 0, -1):
                    teamdiff_layer[x].down()
                    trunc_layer[x].up()
                    teamdiff_layer[x].up(0) # up to left variable
            # repeat until to small update
            if delta <= 0.0001:
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

    def transform_ratings(self, rating_groups, ranks=None):
        rating_groups = list(rating_groups)
        group_size = len(rating_groups)
        # sort rating groups by rank
        if ranks is None:
            ranks = range(group_size)
        elif len(ranks) != group_size:
            raise ValueError('wrong ranks')
        def compare(x, y):
            return cmp(x[1][0], y[1][0])
        sorting = sorted(enumerate(zip(ranks, rating_groups)), compare)
        sorted_groups = [g for x, (r, g) in sorting]
        sorted_ranks = sorted(ranks)
        unsorting_hint = [x for x, (r, g) in sorting]
        # build factor graph
        layers = self.build_factor_graph(sorted_groups, sorted_ranks)
        self.run_schedule(*layers)
        # make result
        rating_layer, team_sizes = layers[0], _team_sizes(sorted_groups)
        transformed_groups = []
        for start, end in zip([0] + team_sizes[:-1], team_sizes):
            group = []
            for f in rating_layer[start:end]:
                group.append(Rating(f.var.mu, f.var.sigma))
            transformed_groups.append(tuple(group))
        def compare(x, y):
            return cmp(x[0], y[0])
        unsorting = sorted(zip(unsorting_hint, transformed_groups), compare)
        return [g for x, g in unsorting]

    def Rating(self, mu=None, sigma=None):
        if mu is None:
            mu = self.mu
        if sigma is None:
            sigma = self.sigma
        return Rating(mu, sigma)


trueskill = TrueSkill()
transform_ratings = trueskill.transform_ratings
