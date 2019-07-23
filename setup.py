# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='mets-mods2teiHeader',
    version='0.0.1',
    description='Convert bibliographic meta data in MODS format to TEI headers',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author='Kay-Michael Würzner',
    author_email='kay-michael.wuerzner@slub-dresden.de',
    license = open('LICENSE').read(),
    packages=find_packages(exclude=('tests', 'docs')),
    package_data={'mets_mods2teiHeader' : ['data/tei_skeleton.xml', 'data/iso15924-utf8-20180827.txt']},
    install_requires=open('requirements.txt').read().split('\n'),
    entry_points={
          'console_scripts': [
              'mods2teiHeader=mets_mods2teiHeader.scripts.mets_mods2teiHeader:cli',
          ]
    },
)
