#!/usr/bin/env python

"""
Setup script for citeproc-py
"""

import io
import os
import re
import sys

from datetime import datetime
from subprocess import Popen, PIPE
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop


PACKAGE = 'citeproc'
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ABSPATH = os.path.join(BASE_PATH, PACKAGE)
VERSION_FILE = os.path.join(PACKAGE_ABSPATH, 'version.py')

VERSION_FORMAT = re.compile(r'v\d+\.\d+\.\d+')

# All external commands are relative to BASE_PATH
os.chdir(BASE_PATH)

# retrieve the version number from git or VERSION_FILE
# inspired by http://dcreager.net/2010/02/10/setuptools-git-version-numbers/
try:
    print('Attempting to get version number from git...')
    git = Popen(['git', 'describe', '--always', '--dirty'],
                stdout=PIPE, stderr=sys.stderr)
    if git.wait() != 0:
        raise OSError
    line, = git.stdout.readlines()
    line = line.strip().decode('ascii')
    __version__ = line[1:] if VERSION_FORMAT.match(line) else line
    __release_date__ = datetime.now().strftime('%b %d %Y, %H:%M:%S')
    with open(VERSION_FILE, 'w') as version_file:
        version_file.write("__version__ = '{}'\n".format(__version__))
        version_file.write("__release_date__ = '{}'\n".format(__release_date__))
except OSError as e:
    print('Assume we are running from a source distribution.')
    # read version from VERSION_FILE
    with open(VERSION_FILE) as version_file:
        code = compile(version_file.read(), VERSION_FILE, 'exec')
        exec(code)


def long_description():
    with open(os.path.join(BASE_PATH, 'README.rst')) as readme:
        result = readme.read()
    result += '\n\n'
    with open(os.path.join(BASE_PATH, 'CHANGES.rst')) as changes:
        result += changes.read()
    return result


CSL_SCHEMA_RNC = 'citeproc/data/schema/csl.rnc'

def convert_rnc():
    import rnc2rng

    filename_root, _ = os.path.splitext(CSL_SCHEMA_RNC)
    root = rnc2rng.load(CSL_SCHEMA_RNC)
    with io.open(filename_root + '.rng', 'w', encoding='utf-8') as rng:
        rnc2rng.dump(root, rng)


class custom_build_py(build_py):
    def run(self):
        convert_rnc()
        build_py.run(self)


class custom_develop(develop):
    def run(self):
        convert_rnc()
        develop.run(self)


setup(
    name='citeproc-py',
    version=__version__,
    cmdclass = dict(build_py=custom_build_py, develop=custom_develop),
    packages=find_packages(),
    package_data={PACKAGE: ['data/locales/*.xml',
                            'data/locales/locales.json',
                            'data/schema/*.rng',
                            'data/styles/*.csl']},
    scripts=['bin/csl_unsorted'],
    setup_requires=['rnc2rng>=2.6.1,!=2.6.2'],
    install_requires=['lxml'],
    provides=[PACKAGE],
    #test_suite='nose.collector',

    author='Brecht Machiels',
    author_email='brecht@mos6581.org',
    description='Citations and bibliography formatter',
    long_description=long_description(),
    url='https://github.com/brechtm/citeproc-py',
    keywords='csl citation html rst bibtex xml',
    license='2-clause BSD License',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Other Environment',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Legal Industry',
        'Intended Audience :: Other Audience',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Documentation',
        'Topic :: Printing',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
