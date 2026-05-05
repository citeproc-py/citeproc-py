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
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
import versioneer

PACKAGE = 'citeproc'
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ABSPATH = os.path.join(BASE_PATH, PACKAGE)
VERSION_FILE = os.path.join(PACKAGE_ABSPATH, 'version.py')


# All external commands are relative to BASE_PATH
os.chdir(BASE_PATH)


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
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass({'build_py': custom_build_py, 'develop': custom_develop}),
    #test_suite='nose.collector',
)
