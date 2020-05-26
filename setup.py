#!/usr/bin/env python
# -*- coding: utf-8 -*-
import warnings
from glob import glob
from os.path import splitext, basename

"""The setup script."""

from setuptools import setup, find_packages

# don't fail if there are problems with the readme (happens within circleci)
try:
    with open('docs/hamilton.md') as readme_file:
        readme = readme_file.read()
except Exception:
    warnings.warn('README.md/docs not found')
    readme = None

REQUIREMENTS_FILES = [
    'requirements.txt'
]


def get_version():
    version_dict = {}
    with open('hamilton/__version__.py') as f:
        exec(f.read(), version_dict)
    return version_dict['__version__']


VERSION = get_version()


def load_requirements():
    requirements = set()
    for requirement_file in REQUIREMENTS_FILES:
        with open(requirement_file) as f:
            requirements.update(line.strip() for line in f)
    return list(requirements)


def load_test_requirements():
    with open('requirements-test.txt') as f:
        return [line.strip() for line in f]


setup_requirements = [
    'pytest-runner',
]

test_requirements = load_test_requirements()

setup(
    name='sf-hamilton',  # there's already a hamilton in pypi
    version=VERSION,
    description='Hamilton, the mirco-framework for creating dataframes.',
    long_description=readme,
    author='skrawczyk@stitchfix.com, elijah.benizzy@stitchfix.com',
    author_email='model-lifecycle-team@stitchfix.com',
    url='https://github.com/stitchfix/hamilton',
    packages=find_packages('hamilton'),
    package_dir={'': 'hamilton'},
    package_data={},
    py_modules=[splitext(basename(path))[0] for path in glob('hamilton/*.py')],
    install_requires=load_requirements(),
    zip_safe=False,
    keywords='hamilton',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',

    # similar to setup_requires, these packages are not added to your venv but are made available
    # during testing
    tests_require=test_requirements,

    # Any packages required when running `python setup.py X` (where X is an alias). These packages
    # are NOT installed as part of the virtualenv (thus not polluting your venv) but instead just
    # made available to the setup.
    setup_requires=setup_requirements,

    # Note that this feature requires pep8 >= v9 and a version of setup tools greater than the
    # default version installed with virtualenv. Make sure to update your tools!
    python_requires='>=3.6',
)
