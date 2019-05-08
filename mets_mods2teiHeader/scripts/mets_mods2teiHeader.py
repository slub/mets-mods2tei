# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import click

from pkg_resources import resource_filename, Requirement

@click.command()
@click.argument('mets', type=click.File('rb'))
def cli(mets):
    """ METS: Input METS XML """
    
    mwd = os.path.abspath(os.path.dirname(mets.name))

    #
    # read in METS

if __name__ == '__main__':
    cli()
