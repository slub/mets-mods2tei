# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import logging
import click
from urllib.request import urlopen

from mets_mods2tei import Mets
from mets_mods2tei import Tei

@click.command()
@click.argument('mets', required=True)
@click.option('-o', '--ocr', is_flag=True, default=False, help="Serialize OCR into resulting TEI")
@click.option('-T', '--text-group', default="FULLTEXT", help="File group which contains the full text")
@click.option('-l', '--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARN', 'ERROR', 'OFF']), default='WARN')
def cli(mets, ocr, text_group, log_level):
    """ METS: File containing or URL pointing to the METS/MODS XML to be converted """

    #
    # logging level
    logging.basicConfig(level=logging.getLevelName(log_level))
    
    #
    # interpret mets argument
    try:
        f = urlopen(mets)
    except:
        f = open(mets, "rb")

    #
    # read in METS
    mets = Mets()
    mets.fulltext_group_name = text_group
    mets.fromfile(f)

    #
    # create TEI (from skeleton)
    tei = Tei()

    tei.fill_from_mets(mets, ocr)

    click.echo(tei.tostring())


if __name__ == '__main__':
    cli()
