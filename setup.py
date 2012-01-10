"""
TrueSkill
~~~~~~~~~

An implementation of the TrueSkill algorithm for Python. TrueSkill is a rating
system between several game players and it is used on Xbox Live to rank and
match players.

>>> from trueskill import Rating
>>> p1, p2, p3, p4 = Rating(), Rating(), Rating(), Rating()
>>> team1, team2, team3 = (p1,), (p2, p3), (p4,)
>>> transform_ratings([team1, team2, team3])

"""
from setuptools import setup


def run_tests():
    from test import suite
    return suite()


setup(
    name='TrueSkill',
    version='0.1-dev',
    url='https://github.com/sublee/trueskill/',
    license='BSD',
    author='Heungsub Lee',
    author_email='h@subl.ee',
    description='TrueSkill system',
    log_description=__doc__,
    packages=['trueskill'],
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Games/Entertainment',
    ],
    test_suite='__main__.run_tests'
)
