# -*- coding: utf-8 -*-
from attest import Tests, assert_hook, raises

from trueskill import *


suite = Tests()


def normalize_rating_groups(rating_groups, precision=3):
    normalized = []
    for ratings in rating_groups:
        for rating in ratings:
            mu = round(rating.mu, precision)
            sigma = round(rating.sigma, precision)
            normalized.append(Rating(mu, sigma))
    return normalized


def generate_teams(sizes, env=None):
    rating_cls = Rating if env is None else env.create_rating
    rating_groups = []
    for size in sizes:
        ratings = []
        for x in xrange(size):
            ratings.append(rating_cls())
        rating_groups.append(tuple(ratings))
    return rating_groups


def parse_ratings(inputs, env=None):
    rating_cls = Rating if env is None else env.create_rating
    ratings = []
    for input in inputs:
        mu, sigma = tuple(map(float, input.split(', ')))
        ratings.append(rating_cls(mu, sigma))
    return ratings


@suite.test
def compare_ratings():
    assert Rating(1, 2) == Rating(1, 2)
    assert Rating(2, 2) > Rating(1, 2)
    assert Rating(3, 2) >= Rating(1, 2)
    assert Rating(0, 2) < Rating(1, 2)
    assert Rating(-1, 2) <= Rating(1, 2)


@suite.test
def unsorted_groups():
    t1, t2, t3 = generate_teams([1, 1, 1])
    rated = rate([t1, t2, t3], [2, 1, 0])
    assert normalize_rating_groups(rated) == \
           parse_ratings(['18.325, 6.656', '25.000, 6.208', '31.675, 6.656'])


@suite.test
def custom_environment():
    env = TrueSkill(draw_probability=.50)
    t1, t2 = generate_teams([1, 1], env=env)
    rated = env.rate([t1, t2])
    assert normalize_rating_groups(rated) == \
           parse_ratings(['30.267, 7.077', '19.733, 7.077'], env=env)


@suite.test
def setup_global_environment():
    try:
        setup(draw_probability=.50)
        t1, t2 = generate_teams([1, 1])
        rated = rate([t1, t2])
        assert normalize_rating_groups(rated) == \
               parse_ratings(['30.267, 7.077', '19.733, 7.077'])
    finally:
        # rollback
        setup()


@suite.test
def invalid_rating_groups():
    with raises(ValueError):
        rate([])
    with raises(ValueError):
        rate([()])
    with raises(ValueError):
        rate([(Rating(),)])
    with raises(ValueError):
        rate([(Rating(),), ()])
    with raises(ValueError):
        quality([])
    with raises(ValueError):
        quality([()])
    with raises(ValueError):
        quality([(Rating(),)])
    with raises(ValueError):
        quality([(Rating(),), ()])
