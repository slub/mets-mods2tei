# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='mets-mods2teiHeader',
    version='0.0.1',
    description='Convert bibliographic meta data in MODS format to TEI headers',
    long_description=readme,
    author='Kay-Michael Würzner',
    author_email='kay-michael.wuerzner@slub-dresden.de',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
    ],
    entry_points={
          'console_scripts': [
              'mods2teiHeader=mets_mods2teiHeader.scripts.mets_mods2teiHeader:cli',
          ]
    },
)
