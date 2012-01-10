import unittest

from trueskill import Rating, transform_ratings


class RatingTestCase(unittest.TestCase):

    def assert_ratings(self, expected, rating_groups, ranks=None, precision=3):
        got = transform_ratings(rating_groups, ranks)
        expected_len, got_len = len(expected), len(got)
        assert expected_len == got_len, \
               'got %d rating groups, but %d is expected' % \
               (got_len, expected_len)
        for x, (expected_group, got_group) in enumerate(zip(expected, got)):
            expected_group_len = len(expected_group)
            got_group_len = len(got_group)
            assert expected_group_len == got_group_len, \
                   'the rating group %d has %d ratings, but %d is expected' % \
                   (x, got_group_len, expected_group_len)
            for expected_rating, got_rating in zip(expected_group, got_group):
                self.assert_rating(expected_rating, got_rating, precision)

    def assert_rating(self, expected, got, precision=3):
        p = precision
        assert round(expected.mu, p) == round(got.mu, p) and \
               round(expected.sigma, p) == round(got.sigma, p), \
               'got mu=%r sigma=%r, but mu=%r sigma=%r is expected' % \
               (got.mu, got.sigma, expected.mu, expected.sigma)

    def teams(self, *sizes):
        for size in sizes:
            ratings = []
            for x in xrange(size):
                ratings.append(Rating())
            yield tuple(ratings)


class TrueSkillTestCase(RatingTestCase):

    def test_1vs1(self):
        t1, t2 = self.teams(1, 1)
        # non-draw
        self.assert_ratings([
            (Rating(29.396, 7.171),),
            (Rating(20.604, 7.171),),
        ], [t1, t2])
        # draw
        self.assert_ratings([
            (Rating(25.000, 6.457),),
            (Rating(25.000, 6.457),),
        ], [t1, t2], [0, 0])


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TrueSkillTestCase))
    return suite
