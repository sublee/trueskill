import doctest
import unittest

import trueskill
from trueskill import TrueSkill, Rating, transform_ratings, match_quality, \
                      setup


class TrueSkillTestCase(unittest.TestCase):

    def assert_ratings(self, expected, rating_groups, ranks=None, precision=3,
                       env=None):
        func = env.transform_ratings if env else transform_ratings
        got = func(rating_groups, ranks)
        flatten = sum(got, ())
        expected_len, got_len = len(expected), len(flatten)
        assert expected_len == got_len, \
               'got %d ratings, but %d is expected' % (got_len, expected_len)
        try:
            for expected_rating, got_rating in zip(expected, flatten):
                self.assert_rating(expected_rating, got_rating, precision)
        except AssertionError, e:
            msg = '\ngot:\n'
            for rating in flatten:
                msg += ' - mu=%r sigma=%r\n' % (rating.mu, rating.sigma)
            msg += 'expected:\n'
            for rating in expected:
                msg += ' - mu=%.{0}f sigma=%.{0}f\n'.format(precision) % \
                       (rating.mu, rating.sigma)
            e.message = msg
            e.args = (msg,)
            raise

    def assert_rating(self, expected, got, precision=3):
        p = precision
        msg = 'got mu=%r sigma=%r, but mu=%r sigma=%r is expected' % \
              (got.mu, got.sigma, expected.mu, expected.sigma)
        for attr in ['mu', 'sigma']:
            self.assert_almost_equals(getattr(expected, attr),
                                      getattr(got, attr), p)

    def assert_match_quality(self, expected, rating_groups, precision=3,
                             env=None):
        func = env.match_quality if env else match_quality
        got = func(rating_groups)
        self.assert_almost_equals(expected, got, precision)

    def assert_almost_equals(self, expected, got, precision=3):
        expected, got = round(expected, precision), round(got, precision)
        try:
            fmt = 'got %.{0}f, but %.{0}f is expected'.format(precision)
            assert expected == got, fmt % (got, expected)
        except AssertionError:
            fmt = '%.{0}f'.format(precision)
            def normalize(f):
                return int((fmt % f).replace('.', ''))
            if abs(normalize(expected) - normalize(got)) == 1:
                # admiss tiny difference
                pass
            else:
                raise

    def parse_ratings(self, text, env=None):
        R = env.Rating if env else Rating
        rv = []
        for line in map(str.strip, text.split('\n')):
            if not line:
                continue
            mu, sigma = tuple(map(float, line.split(', ')))
            rv.append(R(mu, sigma))
        return rv

    def teams(self, *sizes, **kwargs):
        R = kwargs['env'].Rating if 'env' in kwargs else Rating
        for size in sizes:
            ratings = []
            for x in xrange(size):
                ratings.append(R())
            yield tuple(ratings)

    def individual(self, size):
        args = [1] * size
        return list(self.teams(*args))


class FunctionTestCase(TrueSkillTestCase):

    def test_unsorted_groups(self):
        t1, t2, t3 = self.teams(1, 1, 1)
        self.assert_ratings(self.parse_ratings('''
            18.325, 6.656
            25.000, 6.208
            31.675, 6.656
        '''), [t1, t2, t3], [2, 1, 0])

    def test_custom_environment(self):
        env = TrueSkill(draw_probability=.50)
        t1, t2 = self.teams(1, 1, env=env)
        self.assert_ratings(self.parse_ratings('''
            30.267, 7.077
            19.733, 7.077
        '''), [t1, t2], env=env)

    def test_global_environment_customization(self):
        setup(draw_probability=.50)
        t1, t2 = self.teams(1, 1)
        self.assert_ratings(self.parse_ratings('''
            30.267, 7.077
            19.733, 7.077
        '''), [t1, t2])
        # rollback
        setup()

    def test_rating_groups_validation(self):
        try:
            def fail(e=None):
                msg = 'should raise ValueError' + \
                      (' but %s is raised' % type(e).__name__ if e else '')
                assert False, msg
            try:
                transform_ratings([])
                fail()
            except ValueError:
                pass
            try:
                transform_ratings([(Rating(),)])
                fail()
            except ValueError:
                pass
            try:
                transform_ratings([(Rating(),), ()])
                fail()
            except ValueError:
                pass
            try:
                match_quality([])
                fail()
            except ValueError:
                pass
            try:
                match_quality([(Rating(),)])
                fail()
            except ValueError:
                pass
            try:
                match_quality([(Rating(),), ()])
                fail()
            except ValueError:
                pass
        except Exception, e:
            fail(e)


class SimpleTestCase(TrueSkillTestCase):

    def test_1_vs_1(self):
        t1, t2 = self.teams(1, 1)
        self.assert_ratings(self.parse_ratings('''
            29.396, 7.171
            20.604, 7.171
        '''), [t1, t2])
        self.assert_match_quality(0.447, [t1, t2])

    def test_1_vs_1_draw(self):
        t1, t2 = self.teams(1, 1)
        self.assert_ratings(self.parse_ratings('''
            25.000, 6.458
            25.000, 6.458
        '''), [t1, t2], [0, 0])

    def test_2_vs_2(self):
        t1, t2 = self.teams(2, 2)
        self.assert_ratings(self.parse_ratings('''
            28.108, 7.774
            28.108, 7.774
            21.892, 7.774
            21.892, 7.774
        '''), [t1, t2])
        self.assert_match_quality(0.447, [t1, t2])

    def test_2_vs_2_draw(self):
        t1, t2 = self.teams(2, 2)
        self.assert_ratings(self.parse_ratings('''
            25.000, 7.455
            25.000, 7.455
            25.000, 7.455
            25.000, 7.455
        '''), [t1, t2], [0, 0])

    def test_4_vs_4(self):
        t1, t2 = self.teams(4, 4)
        self.assert_ratings(self.parse_ratings('''
            27.198, 8.059
            27.198, 8.059
            27.198, 8.059
            27.198, 8.059
            22.802, 8.059
            22.802, 8.059
            22.802, 8.059
            22.802, 8.059
        '''), [t1, t2])
        self.assert_match_quality(0.447, [t1, t2])


class UnbalancedTeamsTestCase(TrueSkillTestCase):

    def test_1_vs_2(self):
        t1, t2 = self.teams(1, 2)
        self.assert_ratings(self.parse_ratings('''
            33.730, 7.317
            16.270, 7.317
            16.270, 7.317
        '''), [t1, t2])
        self.assert_match_quality(0.135, [t1, t2])

    def test_1_vs_2_draw(self):
        t1, t2 = self.teams(1, 2)
        self.assert_ratings(self.parse_ratings('''
            31.660, 7.138
            18.340, 7.138
            18.340, 7.138
        '''), [t1, t2], [0, 0])

    def test_1_vs_3(self):
        t1, t2 = self.teams(1, 3)
        self.assert_ratings(self.parse_ratings('''
            36.337, 7.527
            13.663, 7.527
            13.663, 7.527
            13.663, 7.527
        '''), [t1, t2])
        self.assert_match_quality(0.012, [t1, t2])

    def test_1_vs_3_draw(self):
        t1, t2 = self.teams(1, 3)
        self.assert_ratings(self.parse_ratings('''
            34.990, 7.455
            15.010, 7.455
            15.010, 7.455
            15.010, 7.455
        '''), [t1, t2], [0, 0])

    def test_1_vs_7(self):
        t1, t2 = self.teams(1, 7)
        self.assert_ratings(self.parse_ratings('''
            40.582, 7.917
            9.418, 7.917
            9.418, 7.917
            9.418, 7.917
            9.418, 7.917
            9.418, 7.917
            9.418, 7.917
            9.418, 7.917
        '''), [t1, t2])
        self.assert_match_quality(0.000, [t1, t2])


class MultipleTeamsTestCase(TrueSkillTestCase):

    def test_individual_3_players(self):
        groups = self.individual(3)
        self.assert_ratings(self.parse_ratings('''
            31.675, 6.656
            25.000, 6.208
            18.325, 6.656
        '''), groups)
        self.assert_match_quality(0.200, groups)

    def test_individual_3_players_draw(self):
        groups = self.individual(3)
        self.assert_ratings(self.parse_ratings('''
            25.000, 5.698
            25.000, 5.695
            25.000, 5.698
        '''), groups, [0] * 3)

    def test_individual_4_players(self):
        groups = self.individual(4)
        self.assert_ratings(self.parse_ratings('''
            33.207, 6.348
            27.401, 5.787
            22.599, 5.787
            16.793, 6.348
        '''), groups)
        self.assert_match_quality(0.089, groups)

    def test_individual_5_players(self):
        groups = self.individual(5)
        self.assert_ratings(self.parse_ratings('''
            34.363, 6.136
            29.058, 5.536
            25.000, 5.420
            20.942, 5.536
            15.637, 6.136
        '''), groups)
        self.assert_match_quality(0.040, groups)

    def test_individual_8_players(self):
        groups = self.individual(8)
        self.assert_ratings(self.parse_ratings('''
            25.000, 4.592
            25.000, 4.583
            25.000, 4.576
            25.000, 4.573
            25.000, 4.573
            25.000, 4.576
            25.000, 4.583
            25.000, 4.592
        '''), groups, [0] * 8)
        self.assert_match_quality(0.004, groups)

    def test_individual_16_players(self):
        groups = self.individual(16)
        self.assert_ratings(self.parse_ratings('''
            40.539, 5.276
            36.810, 4.711
            34.347, 4.524
            32.336, 4.433
            30.550, 4.380
            28.893, 4.349
            27.310, 4.330
            25.766, 4.322
            24.234, 4.322
            22.690, 4.330
            21.107, 4.349
            19.450, 4.380
            17.664, 4.433
            15.653, 4.524
            13.190, 4.711
            9.461, 5.276
        '''), groups)

    def test_2_vs_4_vs_2(self):
        t1 = (Rating(40, 4), Rating(45, 3))
        t2 = (Rating(20, 7), Rating(19, 6), Rating(30, 9), Rating(10, 4))
        t3 = (Rating(50, 5), Rating(30, 2))
        self.assert_ratings(self.parse_ratings('''
            40.877, 3.840
            45.493, 2.934
            19.609, 6.396
            18.712, 5.625
            29.353, 7.673
            9.872, 3.891
            48.830, 4.590
            29.813, 1.976
        '''), [t1, t2, t3], [0, 1, 1])
        self.assert_match_quality(0.367, [t1, t2, t3])


class UpsetTestCase(TrueSkillTestCase):

    def test_1_vs_1_massive_upset_draw(self):
        t1, t2 = (Rating(),), (Rating(50, 12.5),)
        self.assert_ratings(self.parse_ratings('''
            31.662, 7.137
            35.010, 7.910
        '''), [t1, t2], [0, 0])
        self.assert_match_quality(0.110, [t1, t2])

    def test_2_vs_2_upset(self):
        t1 = (Rating(20, 8), Rating(25, 6))
        t2 = (Rating(35, 7), Rating(40, 5))
        self.assert_ratings(self.parse_ratings('''
            29.698, 7.008
            30.455, 5.594
            27.575, 6.346
            36.211, 4.768
        '''), [t1, t2])
        self.assert_match_quality(0.084, [t1, t2])

    def test_3_vs_2_upset(self):
        t1 = (Rating(28, 7), Rating(27, 6), Rating(26, 5))
        t2 = (Rating(30, 4), Rating(31, 3))
        self.assert_ratings(self.parse_ratings('''
            28.658, 6.770
            27.484, 5.856
            26.336, 4.917
            29.785, 3.958
            30.879, 2.983
        '''), [t1, t2], [0, 1])
        self.assert_ratings(self.parse_ratings('''
            21.840, 6.314
            22.474, 5.575
            22.857, 4.757
            32.012, 3.877
            32.132, 2.949
        '''), [t1, t2], [1, 0])
        self.assert_match_quality(0.254, [t1, t2])

    def test_individual_8_players_upset(self):
        t1 = (Rating(10, 8),)
        t2 = (Rating(15, 7),)
        t3 = (Rating(20, 6),)
        t4 = (Rating(25, 5),)
        t5 = (Rating(30, 4),)
        t6 = (Rating(35, 3),)
        t7 = (Rating(40, 2),)
        t8 = (Rating(45, 1),)
        groups = [t1, t2, t3, t4, t5, t6, t7, t8]
        self.assert_ratings(self.parse_ratings('''
            35.135, 4.506
            32.585, 4.037
            31.329, 3.756
            30.984, 3.453
            31.751, 3.064
            34.051, 2.541
            38.263, 1.849
            44.118, 0.983
        '''), groups)
        self.assert_match_quality(0.000, groups)


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(FunctionTestCase))
    suite.addTests(loader.loadTestsFromTestCase(SimpleTestCase))
    suite.addTests(loader.loadTestsFromTestCase(UnbalancedTeamsTestCase))
    suite.addTests(loader.loadTestsFromTestCase(MultipleTeamsTestCase))
    suite.addTests(loader.loadTestsFromTestCase(UpsetTestCase))
    suite.addTests(doctest.DocTestSuite(trueskill))
    return suite
