#!/usr/bin/env python

# Copyright (c) 2016-2019 Chris Reed
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages

setup(
    name="cmdis",
    version="0.1",
    use_scm_version={
        'local_scheme': 'dirty-tag',
        'write_to': 'cmdis/_version.py'
    },
    setup_requires=['setuptools_scm!=1.5.3,!=1.5.4'],
    description="Cortex-M disassembler",
    long_description='',
    author="Chris Reed",
    author_email="flit@me.com",
    url='https://github.com/flit/cmdis',
    license="BSD 3-Clause",
    install_requires=["enum34"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
    ],
    entry_points={
        'console_scripts': [
            'cmdis = cmdis.__main__:main',
        ],
    },
    use_2to3=True,
    packages=find_packages(),
)
