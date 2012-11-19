"""
TrueSkill
~~~~~~~~~

An implementation of the TrueSkill algorithm for Python. TrueSkill is a rating
system among game players and it is used on Xbox Live to rank and match
players.

>>> from trueskill import Rating, rate_1vs1, quality_1vs1
>>> r1, r2 = Rating(mu=25, sigma=8.333), Rating(mu=30, sigma=8.333)
>>> 'Match quality = {:.1%}'.format(quality_1vs1(r1, r2))
'Match quality = 41.6%'
>>> rate_1vs1(r1, r2)
(trueskill.Rating(mu=30.768, sigma=7.030),
 trueskill.Rating(mu=24.232, sigma=7.030))

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
from __future__ import with_statement
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
    author_email='h'r'@'r's'r'u'r'b'r'l'r'.'r'e'r'e',
    url='http://packages.python.org/trueskill',
    description='The TrueSkill rating system',
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
                 'Topic :: Games/Entertainment'],
    install_requires=['distribute'],
    test_suite='trueskilltests',
    tests_require=['pytest'],
    use_2to3=(sys.version_info >= (3,)),
)
