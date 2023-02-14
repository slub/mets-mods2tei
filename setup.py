# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='mets-mods2tei',
    version='0.1.3.post1',
    description='Convert digital documents in METS/MODS format to TEI',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author='Kay-Michael Würzner',
    author_email='kay-michael.wuerzner@slub-dresden.de',
    license_files=('LICENSE',),
    packages=find_packages(exclude=('tests', 'docs')),
    package_data={'mets_mods2tei' : ['data/tei_skeleton.xml', 'data/iso15924-utf8-20180827.txt']},
    install_requires=open('requirements.txt').read().split('\n'),
    python_requires=">=3.6",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Topic :: Text Processing :: Markup :: XML',
    ],
    entry_points={
          'console_scripts': [
              'mm2tei=mets_mods2tei.scripts.mets_mods2tei:cli',
              'mm-update=mets_mods2tei.scripts.update:cli',
          ]
    },
)
