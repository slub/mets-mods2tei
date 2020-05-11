# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='mets-mods2tei',
    version='0.1.1',
    description='Convert digital documents in METS/MODS format to TEI',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author='Kay-Michael Würzner',
    author_email='kay-michael.wuerzner@slub-dresden.de',
    license = open('LICENSE').read(),
    packages=find_packages(exclude=('tests', 'docs')),
    package_data={'mets_mods2tei' : ['data/tei_skeleton.xml', 'data/iso15924-utf8-20180827.txt']},
    install_requires=open('requirements.txt').read().split('\n'),
    entry_points={
          'console_scripts': [
              'mm2tei=mets_mods2tei.scripts.mets_mods2tei:cli',
          ]
    },
)
