# -*- coding: utf-8 -*-
"""
TrueSkill
~~~~~~~~~

An implementation of the TrueSkill algorithm for Python. TrueSkill is a rating
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

- `GitHub repository <http://github.com/sublee/trueskill/>`_
- `development version
  <http://github.com/sublee/trueskill/zipball/master#egg=trueskill-dev>`_

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
import distutils
import os
import re
from setuptools import setup
from setuptools.command.test import test
import sys


# detect the current version
with open('trueskill/__init__.py') as f:
    version = re.search(r'__version__\s*=\s*\'(.+?)\'', f.read()).group(1)
assert version


# use pytest instead
def run_tests(self):
    pyc = re.compile(r'\.pyc|\$py\.class')
    test_file = pyc.sub('.py', __import__(self.test_suite).__file__)
    raise SystemExit(__import__('pytest').main([test_file]))
test.run_tests = run_tests


setup(
    name='trueskill',
    version=version,
    license='BSD',
    author='Heungsub Lee',
    author_email=re.sub('((sub).)(.*)', r'\2@\1.\3', 'sublee'),
    url='http://trueskill.org/',
    description='The video game rating system',
    long_description=__doc__,
    platforms='any',
    packages=['trueskill'],
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.5',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.1',
                 'Programming Language :: Python :: 3.2',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: Implementation :: Jython',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Topic :: Games/Entertainment',
                 'Topic :: Scientific/Engineering :: Mathematics'],
    install_requires=['distribute'],
    test_suite='trueskilltests',
    tests_require=['pytest', 'almost>=0.1.5', 'mpmath>=0.17'],
    use_2to3=(sys.version_info[0] >= 3),
)
