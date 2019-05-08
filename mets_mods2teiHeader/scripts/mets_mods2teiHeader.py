# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import click

from pkg_resources import resource_filename, Requirement

from mets_mods2teiHeader import Mets

@click.command()
@click.argument('mets', type=click.File('rb'))
def cli(mets):
    """ METS: Input METS XML """
    
    mwd = os.path.abspath(os.path.dirname(mets.name))

    #
    # read in METS
    mets = Mets.read(mets)


if __name__ == '__main__':
    cli()
