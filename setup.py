import os
import sys
from setuptools import find_packages, setup

VERSION = "1.0.3"
LONG_DESCRIPTION = """
.. image:: http://pinaxproject.com/pinax-design/patches/pinax-submissions.svg
    :target: https://pypi.python.org/pypi/pinax-submissions/

=================
Pinax Submissions
=================

.. image:: https://img.shields.io/pypi/v/pinax-submissions.svg
    :target: https://pypi.python.org/pypi/pinax-submissions/

\ 

.. image:: https://img.shields.io/circleci/project/github/pinax/pinax-submissions.svg
    :target: https://circleci.com/gh/pinax/pinax-submissions
.. image:: https://img.shields.io/codecov/c/github/pinax/pinax-submissions.svg
    :target: https://codecov.io/gh/pinax/pinax-submissions
.. image:: https://img.shields.io/github/contributors/pinax/pinax-submissions.svg
    :target: https://github.com/pinax/pinax-submissions/graphs/contributors
.. image:: https://img.shields.io/github/issues-pr/pinax/pinax-submissions.svg
    :target: https://github.com/pinax/pinax-submissions/pulls
.. image:: https://img.shields.io/github/issues-pr-closed/pinax/pinax-submissions.svg
    :target: https://github.com/pinax/pinax-submissions/pulls?q=is%3Apr+is%3Aclosed

\ 

.. image:: http://slack.pinaxproject.com/badge.svg
    :target: http://slack.pinaxproject.com/
.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://opensource.org/licenses/MIT/

\ 

``pinax-submissions`` is an app for proposing and reviewing submissions.


Supported Django and Python Versions
------------------------------------
+-----------------+-----+-----+-----+-----+
| Django \ Python | 2.7 | 3.4 | 3.5 | 3.6 |
+=================+=====+=====+=====+=====+
| 1.11            |  *  |  *  |  *  |  *  |
+-----------------+-----+-----+-----+-----+
| 2.0             |     |  *  |  *  |  *  |
+-----------------+-----+-----+-----+-----+
"""


# Publish Helper.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel upload')
    sys.exit()


setup(
    author="Pinax Team",
    author_email="team@pinaxproject.com",
    description="a Django app for proposing and reviewing submissions",
    name="pinax-submissions",
    long_description=LONG_DESCRIPTION,
    version=VERSION,
    url="http://github.com/pinax/pinax-submissions/",
    license="MIT",
    packages=find_packages(),
    package_data={
        "submissions": []
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        "django>=1.11",
        "Markdown>=2.6.3",
        "django-model-utils>=3.1.1",
        "django-appconf>=1.0.2"
    ],
    test_suite="runtests.runtests",
    tests_require=[
    ],
    zip_safe=False
)
