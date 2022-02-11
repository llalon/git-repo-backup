# /usr/bin/env python
# coding: utf-8

from setuptools import setup

setup(
    name='git-repo-backup',
    version='1.0.0',
    description='Backup git repos from Github or Gitlab',
    url='https://github.com/llalon/git-repo-backup',
    author='llalon',
    install_requires=['requests'],
    zip_safe=True,
    packages=['src'],
    entry_points={
        'console_scripts': [
            'git-repo-backup=src.app:main',
        ],
    }
)
