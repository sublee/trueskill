from __future__ import absolute_import

import math

from .mathematics import cdf, pdf, ppf, Gaussian


MU = 25. # initial mean
SIGMA = MU / 3 # initial standard deviation
BETA = SIGMA / 2 # guarantee about an 80% chance of winning
TAU = SIGMA / 100 # dynamic factor
DRAW_PROBABILITY = .10 # draw probability of the game

FEW = 2.222758749e-162


def V(diff, draw_margin):
    """The V function calculates a variation of a mean."""
    x = diff - draw_margin
    cdf_x = cdf(x)
    if cdf_x < FEW:
        return -x
    return pdf(x) / cdf_x


def W(diff, draw_margin):
    """The W function calculates a variation of a standard deviation."""
    x = diff - draw_margin
    cdf_x = cdf(x)
    if cdf_x < FEW:
        return float(diff < 0)
    else:
        v = V(diff, draw_margin)
        return v * (v + x)


def calc_draw_probability(draw_margin, beta, size):
    return 2 * cdf(draw_margin / (math.sqrt(size) * beta)) - 1


def calc_draw_margin(draw_probability, beta, size):
    return ppf((draw_probability + 1) / 2.) * math.sqrt(size) * beta


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


def transform_ratings(rating_groups, ranks=None):
    from .factorgraph import Variable, PriorFactor, \
                                          LikelihoodFactor, SumFactor, \
                                          TruncateFactor
    # flatten
    group_size = len(rating_groups)
    if ranks is None:
        ranks = range(group_size)
    elif len(ranks) != group_size:
        raise ValueError('wrong ranks')
    def cmp_rank(x, y):
        return cmp(x[0], y[0])
    sorted_rating_groups = [g for r, g in \
                            sorted(zip(ranks, rating_groups), cmp_rank)]
    ratings = sum(rating_groups, ())
    size = len(ratings)
    # create variables
    rating_vars = [Variable() for x in xrange(size)]
    perf_vars = [Variable() for x in xrange(size)]
    teamperf_vars = [Variable() for x in xrange(group_size)]
    teamdiff_vars = [Variable() for x in xrange(group_size - 1)]
    team_sizes = [0]
    #
    for group in rating_groups:
        team_sizes.append(len(group) + team_sizes[-1])
    del team_sizes[0]
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
            yield PriorFactor(rating_var, rating, TAU)
    def build_perf_layer():
        for rating_var, perf_var in zip(rating_vars, perf_vars):
            yield LikelihoodFactor(rating_var, perf_var, BETA ** 2)
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
            draw_margin = calc_draw_margin(DRAW_PROBABILITY, BETA, size)
            yield TruncateFactor(teamdiff_var, V, W, draw_margin)
    # build layers
    rating_layer = list(build_rating_layer())
    perf_layer = list(build_perf_layer())
    teamperf_layer = list(build_teamperf_layer())
    teamdiff_layer = list(build_teamdiff_layer())
    trunc_layer = list(build_trunc_layer())
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
    # other black arrows
    for f in teamperf_layer + perf_layer:
        f.up()
    # make result
    rv = []
    for start, end in zip([0] + team_sizes[:-1], team_sizes):
        group = []
        for f in rating_layer[start:end]:
            group.append(Rating(f.var.mu, f.var.sigma))
        rv.append(tuple(group))
    return rv
