"""
TrueSkill
~~~~~~~~~

An implementation of the TrueSkill algorithm for Python. TrueSkill is a rating
system among game players and it is used on Xbox Live to rank and match
players.

>>> from trueskill import Rating, transform_ratings, match_quality
>>> p1, p2, p3, p4 = Rating(), Rating(), Rating(), Rating()
>>> team1, team2, team3 = (p1,), (p2, p3), (p4,)
>>> transform_ratings([team1, team2, team3]) #doctest: +NORMALIZE_WHITESPACE
[(Rating(mu=35.877, sigma=6.791),),
 (Rating(mu=17.867, sigma=7.059), Rating(mu=17.867, sigma=7.059)),
 (Rating(mu=21.255, sigma=7.155),)]
>>> print '%.1f%%' % (match_quality([team1, team2, team3]) * 100)
4.7%

Links
`````

* `GitHub repository <http://github.com/sublee/trueskill/>`_
* `development version
  <http://github.com/sublee/trueskill/zipball/master#egg=trueskill-dev>`_

See Also
````````

* `TrueSkill(TM) Ranking System by Microsoft
  <http://research.microsoft.com/en-us/projects/trueskill/>`_
* `"Computing Your Skill" by Jeff Moser <http://bit.ly/moserware-trueskill>`_
* `"The Math Behind TrueSkill" by Jeff Moser <http://bit.ly/trueskill-math>`_
* `TrueSkill Calcurator by Microsoft
  <http://atom.research.microsoft.com/trueskill/rankcalculator.aspx>`_

"""
from setuptools import setup


def run_tests():
    from test import suite
    return suite()


setup(
    name='trueskill',
    version='0.1.2',
    url='https://github.com/sublee/trueskill/',
    license='BSD',
    author='Heungsub Lee',
    author_email='h@subl.ee',
    description='A Bayesian Skill Rating System',
    long_description=__doc__,
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
