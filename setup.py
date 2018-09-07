# -*- coding: utf-8 -*-
"""
TrueSkill
~~~~~~~~~

An implementation of the TrueSkill algorithm for Python.  TrueSkill is a rating
system among game players and it is used on Xbox Live to rank and match
players.

.. sourcecode:: python

   from trueskill import Rating, quality_1vs1, rate_1vs1
   alice, bob = Rating(25), Rating(30)  # assign Alice and Bob's ratings
   if quality_1vs1(alice, bob) < 0.50:
       print('This match seems to be not so fair')
   alice, bob = rate_1vs1(alice, bob)  # update the ratings after the match

Links
`````

Documentation
   http://trueskill.org/
GitHub:
   http://github.com/sublee/trueskill
Mailing list:
   trueskill@librelist.com
List archive:
   http://librelist.com/browser/trueskill
Continuous integration (Travis CI)
   https://travis-ci.org/sublee/trueskill

   .. image:: https://api.travis-ci.org/sublee/trueskill.png

See Also
````````

- `TrueSkill(TM) Ranking System by Microsoft
  <http://research.microsoft.com/en-us/projects/trueskill/>`_
- `"Computing Your Skill" by Jeff Moser <http://bit.ly/moserware-trueskill>`_
- `"The Math Behind TrueSkill" by Jeff Moser <http://bit.ly/trueskill-math>`_
- `TrueSkill Calcurator by Microsoft
  <http://atom.research.microsoft.com/trueskill/rankcalculator.aspx>`_

"""
from __future__ import with_statement

import os

from setuptools import setup
from setuptools.command.test import test


# include __about__.py.
__dir__ = os.path.dirname(__file__)
about = {}
with open(os.path.join(__dir__, 'trueskill', '__about__.py')) as f:
    exec(f.read(), about)


# use pytest instead.
def run_tests(self):
    raise SystemExit(__import__('pytest').main(['-v']))
test.run_tests = run_tests


setup(
    name='trueskill',
    version=about['__version__'],
    license=about['__license__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    description=about['__description__'],
    long_description=__doc__,
    platforms='any',
    packages=['trueskill'],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: Implementation :: Jython',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Topic :: Games/Entertainment',
                 'Topic :: Scientific/Engineering :: Mathematics'],
    install_requires=['six'],
    tests_require=['pytest>=2.8.5', 'almost>=0.1.5', 'mpmath>=0.17'],
    test_suite='...',
)
