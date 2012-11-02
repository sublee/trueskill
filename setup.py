"""
TrueSkill
~~~~~~~~~

An implementation of the TrueSkill algorithm for Python. TrueSkill is a rating
system among game players and it is used on Xbox Live to rank and match
players.

>>> from trueskill import Rating, rate_1vs1, quality
>>> r1, r2 = Rating(mu=25, sigma=8.333333), Rating(mu=30, sigma=8.333333)
>>> print 'Match quality = %.1f%%' % (quality_1vs1(r1, r2) * 100)
Match quality = 40%
>>> rate_1vs1(r1, r2)
(Rating(mu=, sigma=), Rating(mu=, sigma=))

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

import trueskill


setup(
    name=trueskill.__name__,
    version=trueskill.__version__,
    license=trueskill.__license__,
    author=trueskill.__author__,
    author_email=trueskill.__author_email__,
    url=trueskill.__url__,
    description='A Bayesian Skill Rating System',
    long_description=__doc__,
    packages=['trueskill'],
    zip_safe=False,
    platforms='any',
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Topic :: Games/Entertainment'],
    install_requires=['distribute'],
    test_suite='trueskilltests.suite',
    test_loader='attest:auto_reporter.test_loader',
    tests_require=['Attest'],
)
