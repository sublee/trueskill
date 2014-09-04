# -*- coding: utf-8 -*-
from __future__ import with_statement

from almost import Approximate
from pytest import deprecated_call, raises

from conftest import various_backends
import trueskill as t
from trueskill import (
    Rating, TrueSkill, quality, quality_1vs1, rate, rate_1vs1, setup)


inf = float('inf')
nan = float('nan')


class almost(Approximate):

    def normalize(self, value):
        if isinstance(value, Rating):
            return self.normalize(tuple(value))
        elif isinstance(value, list):
            try:
                if isinstance(value[0][0], Rating):
                    # flatten transformed ratings
                    return list(sum(value, ()))
            except (TypeError, IndexError):
                pass
        return super(almost, self).normalize(value)

    @classmethod
    def wrap(cls, f, *args, **kwargs):
        return lambda *a, **k: cls(f(*a, **k), *args, **kwargs)


_rate = almost.wrap(rate)
_rate_1vs1 = almost.wrap(rate_1vs1)
_quality = almost.wrap(quality)
_quality_1vs1 = almost.wrap(quality_1vs1)


# usage


def test_compatibility_with_another_rating_systems():
    """All rating system modules should implement ``rate_1vs1`` and
    ``quality_1vs1`` to provide shortcuts for 1 vs 1 simple competition games.
    """
    r1, r2 = Rating(30, 3), Rating(20, 2)
    assert quality_1vs1(r1, r2) == quality([(r1,), (r2,)])
    rated = rate([(r1,), (r2,)])
    assert rate_1vs1(r1, r2) == (rated[0][0], rated[1][0])
    rated = rate([(r1,), (r2,)], [0, 0])
    assert rate_1vs1(r1, r2, drawn=True) == (rated[0][0], rated[1][0])


def test_compare_ratings():
    assert Rating(1, 2) == Rating(1, 2)
    assert Rating(1, 2) != Rating(1, 3)
    assert Rating(2, 2) > Rating(1, 2)
    assert Rating(3, 2) >= Rating(1, 2)
    assert Rating(0, 2) < Rating(1, 2)
    assert Rating(-1, 2) <= Rating(1, 2)


def test_rating_to_number():
    assert int(Rating(1, 2)) == 1
    assert float(Rating(1.1, 2)) == 1.1
    assert complex(Rating(1.2, 2)) == 1.2 + 0j
    try:
        assert long(Rating(1, 2)) == long(1)
    except NameError:
        # Python 3 doesn't have `long` anymore
        pass


def test_unsorted_groups():
    t1, t2, t3 = generate_teams([1, 1, 1])
    rated = rate([t1, t2, t3], [2, 1, 0])
    assert almost(rated) == \
        [(18.325, 6.656), (25.000, 6.208), (31.675, 6.656)]


def test_custom_environment():
    env = TrueSkill(draw_probability=.50)
    t1, t2 = generate_teams([1, 1], env=env)
    rated = env.rate([t1, t2])
    assert almost(rated) == [(30.267, 7.077), (19.733, 7.077)]


def test_setup_global_environment():
    try:
        setup(draw_probability=.50)
        t1, t2 = generate_teams([1, 1])
        rated = rate([t1, t2])
        assert almost(rated) == [(30.267, 7.077), (19.733, 7.077)]
    finally:
        # rollback
        setup()


def test_invalid_rating_groups():
    env = TrueSkill()
    with raises(ValueError):
        env.validate_rating_groups([])
    with raises(ValueError):
        env.validate_rating_groups([()])
    # need multiple groups not just one
    with raises(ValueError):
        env.validate_rating_groups([(Rating(),)])
    # empty group is not allowed
    with raises(ValueError):
        env.validate_rating_groups([(Rating(),), ()])
    # all groups should be same structure
    with raises(TypeError):
        env.validate_rating_groups([(Rating(),), {0: Rating()}])


def test_deprecated_methods():
    env = TrueSkill()
    r1, r2, r3 = Rating(), Rating(), Rating()
    deprecated_call(t.transform_ratings, [(r1,), (r2,), (r3,)])
    deprecated_call(t.match_quality, [(r1,), (r2,), (r3,)])
    deprecated_call(env.Rating)
    deprecated_call(env.transform_ratings, [(r1,), (r2,), (r3,)])
    deprecated_call(env.match_quality, [(r1,), (r2,), (r3,)])
    deprecated_call(env.rate_1vs1, r1, r2)
    deprecated_call(env.quality_1vs1, r1, r2)
    deprecated_call(lambda: Rating().exposure)
    dyn = TrueSkill(draw_probability=t.dynamic_draw_probability)
    deprecated_call(dyn.rate, [(r1,), (r2,)])


def test_deprecated_individual_rating_groups():
    r1, r2, r3 = Rating(50, 1), Rating(10, 5), Rating(15, 5)
    with raises(TypeError):
        deprecated_call(rate, [r1, r2, r3])
    with raises(TypeError):
        deprecated_call(quality, [r1, r2, r3])
    assert t.transform_ratings([r1, r2, r3]) == rate([(r1,), (r2,), (r3,)])
    assert t.match_quality([r1, r2, r3]) == quality([(r1,), (r2,), (r3,)])
    deprecated_call(t.transform_ratings, [r1, r2, r3])
    deprecated_call(t.match_quality, [r1, r2, r3])


def test_rating_tuples():
    r1, r2, r3 = Rating(), Rating(), Rating()
    rated = rate([(r1, r2), (r3,)])
    assert len(rated) == 2
    assert isinstance(rated[0], tuple)
    assert isinstance(rated[1], tuple)
    assert len(rated[0]) == 2
    assert len(rated[1]) == 1
    assert isinstance(rated[0][0], Rating)


def test_rating_dicts():
    class Player(object):
        def __init__(self, name, rating, team):
            self.name = name
            self.rating = rating
            self.team = team
    p1 = Player('Player A', Rating(), 0)
    p2 = Player('Player B', Rating(), 0)
    p3 = Player('Player C', Rating(), 1)
    rated = rate([{p1: p1.rating, p2: p2.rating}, {p3: p3.rating}])
    assert len(rated) == 2
    assert isinstance(rated[0], dict)
    assert isinstance(rated[1], dict)
    assert len(rated[0]) == 2
    assert len(rated[1]) == 1
    assert p1 in rated[0]
    assert p2 in rated[0]
    assert p3 in rated[1]
    assert p1 not in rated[1]
    assert p2 not in rated[1]
    assert p3 not in rated[0]
    assert isinstance(rated[0][p1], Rating)
    p1.rating = rated[p1.team][p1]
    p2.rating = rated[p2.team][p2]
    p3.rating = rated[p3.team][p3]


def test_dont_use_0_for_min_delta():
    with raises(ValueError):
        rate([(Rating(),), (Rating(),)], min_delta=0)


def test_list_instead_of_tuple():
    r1, r2 = Rating(), Rating()
    assert rate([[r1], [r2]]) == rate([(r1,), (r2,)])
    assert quality([[r1], [r2]]) == quality([(r1,), (r2,)])


def test_backend():
    env = TrueSkill(backend=(NotImplemented, NotImplemented, NotImplemented))
    with raises(TypeError):
        env.rate_1vs1(Rating(), Rating())
    with raises(ValueError):
        # '__not_defined__' backend is not defined
        TrueSkill(backend='__not_defined__')


# algorithm


def generate_teams(sizes, env=None):
    rating_cls = Rating if env is None else env.create_rating
    rating_groups = []
    for size in sizes:
        ratings = []
        for x in range(size):
            ratings.append(rating_cls())
        rating_groups.append(tuple(ratings))
    return rating_groups


def generate_individual(size, env=None):
    return generate_teams([1] * size, env=env)


@various_backends
def test_n_vs_n():
    # 1 vs 1
    t1, t2 = generate_teams([1, 1])
    assert _quality([t1, t2]) == 0.447
    assert _rate([t1, t2]) == [(29.396, 7.171), (20.604, 7.171)]
    assert _rate([t1, t2], [0, 0]) == [(25.000, 6.458), (25.000, 6.458)]
    # 2 vs 2
    t1, t2 = generate_teams([2, 2])
    assert _quality([t1, t2]) == 0.447
    assert _rate([t1, t2]) == \
        [(28.108, 7.774), (28.108, 7.774), (21.892, 7.774), (21.892, 7.774)]
    assert _rate([t1, t2], [0, 0]) == \
        [(25.000, 7.455), (25.000, 7.455), (25.000, 7.455), (25.000, 7.455)]
    # 4 vs 4
    t1, t2 = generate_teams([4, 4])
    assert _quality([t1, t2]) == 0.447
    assert _rate([t1, t2]) == \
        [(27.198, 8.059), (27.198, 8.059), (27.198, 8.059), (27.198, 8.059),
         (22.802, 8.059), (22.802, 8.059), (22.802, 8.059), (22.802, 8.059)]


@various_backends
def test_1_vs_n():
    t1, = generate_teams([1])
    # 1 vs 2
    t2, = generate_teams([2])
    assert _quality([t1, t2]) == 0.135
    assert _rate([t1, t2]) == \
        [(33.730, 7.317), (16.270, 7.317), (16.270, 7.317)]
    assert _rate([t1, t2], [0, 0]) == \
        [(31.660, 7.138), (18.340, 7.138), (18.340, 7.138)]
    # 1 vs 3
    t2, = generate_teams([3])
    assert _quality([t1, t2]) == 0.012
    assert _rate([t1, t2]) == \
        [(36.337, 7.527), (13.663, 7.527), (13.663, 7.527), (13.663, 7.527)]
    assert almost(rate([t1, t2], [0, 0]), 2) == \
        [(34.990, 7.455), (15.010, 7.455), (15.010, 7.455), (15.010, 7.455)]
    # 1 vs 7
    t2, = generate_teams([7])
    assert _quality([t1, t2]) == 0
    assert _rate([t1, t2]) == \
        [(40.582, 7.917), (9.418, 7.917), (9.418, 7.917), (9.418, 7.917),
         (9.418, 7.917), (9.418, 7.917), (9.418, 7.917), (9.418, 7.917)]


@various_backends
def test_individual():
    # 3 players
    players = generate_individual(3)
    assert _quality(players) == 0.200
    assert _rate(players) == \
        [(31.675, 6.656), (25.000, 6.208), (18.325, 6.656)]
    assert _rate(players, [0] * 3) == \
        [(25.000, 5.698), (25.000, 5.695), (25.000, 5.698)]
    # 4 players
    players = generate_individual(4)
    assert _quality(players) == 0.089
    assert _rate(players) == \
        [(33.207, 6.348), (27.401, 5.787), (22.599, 5.787), (16.793, 6.348)]
    # 5 players
    players = generate_individual(5)
    assert _quality(players) == 0.040
    assert _rate(players) == \
        [(34.363, 6.136), (29.058, 5.536), (25.000, 5.420), (20.942, 5.536),
         (15.637, 6.136)]
    # 8 players
    players = generate_individual(8)
    assert _quality(players) == 0.004
    assert _rate(players, [0] * 8) == \
        [(25.000, 4.592), (25.000, 4.583), (25.000, 4.576), (25.000, 4.573),
         (25.000, 4.573), (25.000, 4.576), (25.000, 4.583), (25.000, 4.592)]
    # 16 players
    players = generate_individual(16)
    assert _rate(players) == \
        [(40.539, 5.276), (36.810, 4.711), (34.347, 4.524), (32.336, 4.433),
         (30.550, 4.380), (28.893, 4.349), (27.310, 4.330), (25.766, 4.322),
         (24.234, 4.322), (22.690, 4.330), (21.107, 4.349), (19.450, 4.380),
         (17.664, 4.433), (15.653, 4.524), (13.190, 4.711), (9.461, 5.276)]


@various_backends
def test_multiple_teams():
    # 2 vs 4 vs 2
    t1 = (Rating(40, 4), Rating(45, 3))
    t2 = (Rating(20, 7), Rating(19, 6), Rating(30, 9), Rating(10, 4))
    t3 = (Rating(50, 5), Rating(30, 2))
    assert _quality([t1, t2, t3]) == 0.367
    assert _rate([t1, t2, t3], [0, 1, 1]) == \
        [(40.877, 3.840), (45.493, 2.934), (19.609, 6.396), (18.712, 5.625),
         (29.353, 7.673), (9.872, 3.891), (48.830, 4.590), (29.813, 1.976)]
    # 1 vs 2 vs 1
    t1 = (Rating(),)
    t2 = (Rating(), Rating())
    t3 = (Rating(),)
    assert _quality([t1, t2, t3]) == 0.047


@various_backends
def test_upset():
    # 1 vs 1
    t1, t2 = (Rating(),), (Rating(50, 12.5),)
    assert _quality([t1, t2]) == 0.110
    assert _rate([t1, t2], [0, 0]) == [(31.662, 7.137), (35.010, 7.910)]
    # 2 vs 2
    t1 = (Rating(20, 8), Rating(25, 6))
    t2 = (Rating(35, 7), Rating(40, 5))
    assert _quality([t1, t2]) == 0.084
    assert _rate([t1, t2]) == \
        [(29.698, 7.008), (30.455, 5.594), (27.575, 6.346), (36.211, 4.768)]
    # 3 vs 2
    t1 = (Rating(28, 7), Rating(27, 6), Rating(26, 5))
    t2 = (Rating(30, 4), Rating(31, 3))
    assert _quality([t1, t2]) == 0.254
    assert _rate([t1, t2], [0, 1]) == \
        [(28.658, 6.770), (27.484, 5.856), (26.336, 4.917), (29.785, 3.958),
         (30.879, 2.983)]
    assert _rate([t1, t2], [1, 0]) == \
        [(21.840, 6.314), (22.474, 5.575), (22.857, 4.757), (32.012, 3.877),
         (32.132, 2.949)]
    # 8 players
    players = [(Rating(10, 8),), (Rating(15, 7),), (Rating(20, 6),),
               (Rating(25, 5),), (Rating(30, 4),), (Rating(35, 3),),
               (Rating(40, 2),), (Rating(45, 1),)]
    assert _quality(players) == 0.000
    assert _rate(players) == \
        [(35.135, 4.506), (32.585, 4.037), (31.329, 3.756), (30.984, 3.453),
         (31.751, 3.064), (34.051, 2.541), (38.263, 1.849), (44.118, 0.983)]


@various_backends
def test_partial_play():
    t1, t2 = (Rating(),), (Rating(), Rating())
    # each results from C# Skills:
    assert rate([t1, t2], weights=[(1,), (1, 1)]) == rate([t1, t2])
    assert _rate([t1, t2], weights=[(1,), (1, 1)]) == \
        [(33.730, 7.317), (16.270, 7.317), (16.270, 7.317)]
    assert _rate([t1, t2], weights=[(0.5,), (0.5, 0.5)]) == \
        [(33.939, 7.312), (16.061, 7.312), (16.061, 7.312)]
    assert _rate([t1, t2], weights=[(1,), (0, 1)]) == \
        [(29.440, 7.166), (25.000, 8.333), (20.560, 7.166)]
    assert _rate([t1, t2], weights=[(1,), (0.5, 1)]) == \
        [(32.417, 7.056), (21.291, 8.033), (17.583, 7.056)]
    # match quality of partial play
    t1, t2, t3 = (Rating(),), (Rating(), Rating()), (Rating(),)
    assert _quality([t1, t2, t3], [(1,), (0.25, 0.75), (1,)]) == 0.2
    assert _quality([t1, t2, t3], [(1,), (0.8, 0.9), (1,)]) == 0.0809


@various_backends
def test_partial_play_with_weights_dict():
    t1, t2 = (Rating(),), (Rating(), Rating())
    assert rate([t1, t2], weights={(0, 0): 0.5, (1, 0): 0.5, (1, 1): 0.5}) == \
        rate([t1, t2], weights=[[0.5], [0.5, 0.5]])
    assert rate([t1, t2], weights={(1, 0): 0}) == \
        rate([t1, t2], weights=[[1], [0, 1]])
    assert rate([t1, t2], weights={(1, 0): 0.5}) == \
        rate([t1, t2], weights=[[1], [0.5, 1]])


@various_backends
def test_microsoft_research_example():
    # http://research.microsoft.com/en-us/projects/trueskill/details.aspx
    alice, bob, chris, darren, eve, fabien, george, hillary = \
        Rating(), Rating(), Rating(), Rating(), \
        Rating(), Rating(), Rating(), Rating()
    _rated = rate([{'alice': alice}, {'bob': bob}, {'chris': chris},
                   {'darren': darren}, {'eve': eve}, {'fabien': fabien},
                   {'george': george}, {'hillary': hillary}])
    rated = {}
    list(map(rated.update, _rated))
    assert almost(rated['alice']) == (36.771, 5.749)
    assert almost(rated['bob']) == (32.242, 5.133)
    assert almost(rated['chris']) == (29.074, 4.943)
    assert almost(rated['darren']) == (26.322, 4.874)
    assert almost(rated['eve']) == (23.678, 4.874)
    assert almost(rated['fabien']) == (20.926, 4.943)
    assert almost(rated['george']) == (17.758, 5.133)
    assert almost(rated['hillary']) == (13.229, 5.749)


@various_backends
def test_dynamic_draw_probability():
    from trueskillhelpers import calc_dynamic_draw_probability as calc
    def assert_predictable_draw_probability(r1, r2, drawn=False):
        dyn = TrueSkill(draw_probability=t.dynamic_draw_probability)
        sta = TrueSkill(draw_probability=calc((r1,), (r2,), dyn))
        assert dyn.rate_1vs1(r1, r2, drawn) == sta.rate_1vs1(r1, r2, drawn)
    assert_predictable_draw_probability(Rating(100), Rating(10))
    assert_predictable_draw_probability(Rating(10), Rating(100))
    assert_predictable_draw_probability(Rating(10), Rating(100), drawn=True)
    assert_predictable_draw_probability(Rating(25), Rating(25))
    assert_predictable_draw_probability(Rating(25), Rating(25), drawn=True)
    assert_predictable_draw_probability(Rating(-25), Rating(125))
    assert_predictable_draw_probability(Rating(125), Rating(-25))
    assert_predictable_draw_probability(Rating(-25), Rating(125), drawn=True)
    assert_predictable_draw_probability(Rating(25, 10), Rating(25, 0.1))


# functions


@various_backends
def test_exposure():
    env = TrueSkill()
    assert env.expose(env.create_rating()) == 0
    env = TrueSkill(1000, 200)
    assert env.expose(env.create_rating()) == 0


# mathematics


def test_valid_gaussian():
    from trueskill.mathematics import Gaussian
    with raises(TypeError):  # sigma argument is needed
        Gaussian(0)
    with raises(ValueError):  # sigma**2 should be greater than 0
        Gaussian(0, 0)


def test_valid_matrix():
    from trueskill.mathematics import Matrix
    with raises(TypeError):  # src must be a list or dict or callable
        Matrix(None)
    with raises(ValueError):  # src must be a rectangular array of numbers
        Matrix([])
    with raises(ValueError):  # src must be a rectangular array of numbers
        Matrix([[1, 2, 3], [4, 5]])
    with raises(TypeError):
        # A callable src must return an interable which generates a tuple
        # containing coordinate and value
        Matrix(lambda: None)


def test_matrix_from_dict():
    from trueskill.mathematics import Matrix
    mat = Matrix({(0, 0): 1, (4, 9): 1})
    assert mat.height == 5
    assert mat.width == 10
    assert mat[0][0] == 1
    assert mat[0][1] == 0
    assert mat[4][9] == 1
    assert mat[4][8] == 0


def test_matrix_from_item_generator():
    from trueskill.mathematics import Matrix
    def gen_matrix(height, width):
        yield (0, 0), 1
        yield (height - 1, width - 1), 1
    mat = Matrix(gen_matrix, 5, 10)
    assert mat.height == 5
    assert mat.width == 10
    assert mat[0][0] == 1
    assert mat[0][1] == 0
    assert mat[4][9] == 1
    assert mat[4][8] == 0
    with raises(TypeError):
        # A callable src must call set_height and set_width if the size is
        # non-deterministic
        Matrix(gen_matrix)
    def gen_and_set_size_matrix(set_height, set_width):
        set_height(5)
        set_width(10)
        return [((0, 0), 1), ((4, 9), 1)]
    mat = Matrix(gen_and_set_size_matrix)
    assert mat.height == 5
    assert mat.width == 10
    assert mat[0][0] == 1
    assert mat[0][1] == 0
    assert mat[4][9] == 1
    assert mat[4][8] == 0


def test_matrix_operations():
    from trueskill.mathematics import Matrix
    assert Matrix([[1, 2], [3, 4]]).inverse() == \
        Matrix([[-2.0, 1.0], [1.5, -0.5]])
    assert Matrix([[1, 2], [3, 4]]).determinant() == -2
    assert Matrix([[1, 2], [3, 4]]).adjugate() == Matrix([[4, -2], [-3, 1]])
    with raises(ValueError):  # Bad size
        assert Matrix([[1, 2], [3, 4]]) * Matrix([[5, 6]])
    assert Matrix([[1, 2], [3, 4]]) * Matrix([[5, 6, 7], [8, 9, 10]]) == \
        Matrix([[21, 24, 27], [47, 54, 61]])
    with raises(ValueError):  # Must be same size
        Matrix([[1, 2], [3, 4]]) + Matrix([[5, 6, 7], [8, 9, 10]])
    assert Matrix([[1, 2], [3, 4]]) + Matrix([[5, 6], [7, 8]]) == \
        Matrix([[6, 8], [10, 12]])


# reported bugs


@various_backends
def test_issue3():
    """The `issue #3`_, opened by @youknowone.

    These inputs led to ZeroDivisionError before 0.1.4. Also another TrueSkill
    implementations cannot calculate this case.

    .. _issue #3: https://github.com/sublee/trueskill/issues/3
    """
    # @konikos's case 1
    t1 = (Rating(42.234, 3.728), Rating(43.290, 3.842))
    t2 = (Rating(16.667, 0.500), Rating(16.667, 0.500), Rating(16.667, 0.500),
          Rating(16.667, 0.500), Rating(16.667, 0.500), Rating(16.667, 0.500),
          Rating(16.667, 0.500), Rating(16.667, 0.500), Rating(16.667, 0.500),
          Rating(16.667, 0.500), Rating(16.667, 0.500), Rating(16.667, 0.500),
          Rating(16.667, 0.500), Rating(16.667, 0.500), Rating(16.667, 0.500))
    rate([t1, t2], [6, 5])
    # @konikos's case 2
    t1 = (Rating(25.000, 0.500), Rating(25.000, 0.500), Rating(25.000, 0.500),
          Rating(25.000, 0.500), Rating(33.333, 0.500), Rating(33.333, 0.500),
          Rating(33.333, 0.500), Rating(33.333, 0.500), Rating(41.667, 0.500),
          Rating(41.667, 0.500), Rating(41.667, 0.500), Rating(41.667, 0.500))
    t2 = (Rating(42.234, 3.728), Rating(43.291, 3.842))
    rate([t1, t2], [0, 28])


@various_backends(['scipy'])
def test_issue4():
    """The `issue #4`_, opened by @sublee.

    numpy.float64 handles floating-point error by different way. For example,
    it can just warn RuntimeWarning on n/0 problem instead of throwing
    ZeroDivisionError.

    .. _issue #4: https://github.com/sublee/trueskill/issues/4
    """
    import numpy
    r1, r2 = Rating(105.247, 0.439), Rating(27.030, 0.901)
    # make numpy to raise FloatingPointError instead of warning
    # RuntimeWarning
    old_settings = numpy.seterr(divide='raise')
    try:
        rate([(r1,), (r2,)])
    finally:
        numpy.seterr(**old_settings)


@various_backends([None, 'scipy'])
def test_issue5(backend):
    """The `issue #5`_, opened by @warner121.

    This error occurs when a winner has too low rating than a loser. Basically
    Python cannot calculate correct result but mpmath_ can. I added ``backend``
    option to :class:`TrueSkill` class. If it is set to 'mpmath' then the
    problem will have gone.

    The result of TrueSkill calculator by Microsoft is N(-273.092, 2.683) and
    N(-75.830, 2.080), of C# Skills by Moserware is N(NaN, 2.6826) and
    N(NaN, 2.0798). I choose Microsoft's result as an expectation for the test
    suite.

    .. _issue #5: https://github.com/sublee/trueskill/issues/5
    .. _mpmath: http://mpmath.googlecode.com/
    """
    assert _quality_1vs1(Rating(-323.263, 2.965), Rating(-48.441, 2.190)) == 0
    with raises(FloatingPointError):
        rate_1vs1(Rating(-323.263, 2.965), Rating(-48.441, 2.190))
    assert _quality_1vs1(Rating(), Rating(1000)) == 0
    with raises(FloatingPointError):
        rate_1vs1(Rating(), Rating(1000))


@various_backends(['mpmath'])
def test_issue5_with_mpmath():
    _rate_1vs1 = almost.wrap(rate_1vs1, 0)
    assert _quality_1vs1(Rating(-323.263, 2.965), Rating(-48.441, 2.190)) == 0
    assert _rate_1vs1(Rating(-323.263, 2.965), Rating(-48.441, 2.190)) == \
        [(-273.361, 2.683), (-75.683, 2.080)]
    assert _quality_1vs1(Rating(), Rating(1000)) == 0
    assert _rate_1vs1(Rating(), Rating(1000)) == \
        [(415.298, 6.455), (609.702, 6.455)]


@various_backends(['mpmath'])
def test_issue5_with_more_extreme():
    """If the input is more extreme, 'mpmath' backend also made an exception.
    But we can avoid the problem with higher precision.
    """
    import mpmath
    try:
        dps = mpmath.mp.dps
        with raises(FloatingPointError):
            rate_1vs1(Rating(), Rating(1000000))
        mpmath.mp.dps = 50
        assert almost(rate_1vs1(Rating(), Rating(1000000)), prec=-1) == \
            [(400016.896, 6.455), (600008.104, 6.455)]
        with raises(FloatingPointError):
            rate_1vs1(Rating(), Rating(1000000000000))
        mpmath.mp.dps = 100
        assert almost(rate_1vs1(Rating(), Rating(1000000000000)), prec=-7) == \
            [(400001600117.693, 6.455), (599998399907.307, 6.455)]
    finally:
        mpmath.mp.dps = dps


def test_issue9_weights_dict_with_object_keys():
    """The `issue #9`_, opened by @.

    .. _issue #9: https://github.com/sublee/trueskill/issues/9
    """
    class Player(object):
        def __init__(self, rating, team):
            self.rating = rating
            self.team = team
    p1 = Player(Rating(), 0)
    p2 = Player(Rating(), 0)
    p3 = Player(Rating(), 1)
    teams = [{p1: p1.rating, p2: p2.rating}, {p3: p3.rating}]
    rated = rate(teams, weights={(0, p1): 1, (0, p2): 0.5, (1, p3): 1})
    assert rated[0][p1].mu > rated[0][p2].mu
    assert rated[0][p1].sigma < rated[0][p2].sigma
    assert rated[0][p1].sigma == rated[1][p3].sigma
