# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys
import os
import logging
import click
from urllib.request import urlopen

from mets_mods2tei import Mets
from mets_mods2tei import Tei

@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.argument('mets', required=True)
@click.option('-O', '--output', default="-", type=click.File("wb"), help="File path to write TEI output to")
@click.option('-o', '--ocr', is_flag=True, default=False, help="Serialize OCR into resulting TEI")
@click.option('-T', '--text-group', default="FULLTEXT", help="File group which contains the full-text")
@click.option('-I', '--img-group', default="DEFAULT", help="File group which contains the images")
@click.option('-r', '--add-refs', type=click.Choice(['page', 'line']), multiple=True, default=['page'])
@click.option('-l', '--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARN', 'ERROR', 'OFF']), default='WARN')
def cli(mets, output, ocr, text_group, img_group, add_refs, log_level):
    """METS: File containing or URL pointing to the METS/MODS XML to be converted

    Parse given METS and its meta-data, and convert it to TEI.

    If `--ocr` is given, then also read the ALTO full-text files
    from the fileGrp in `--text-group`, and convert page contents
    accordingly (in physical order).

    Decorate page boundaries with image and page numbers. Moreover,
    if `--add-refs` contains `page`, then reference the corresponding
    base image files (by file name) from `--img-group`. Likewise,
    if `--add-refs` contains `line`, then reference the corresponding
    textline segments (by XML ID) from `--text-group`.

    Output XML to `--output (use '-' for stdout), log to stderr.`
    """

    #
    # logging level
    logging.basicConfig(level=logging.getLevelName(log_level), stream=sys.stderr)
    
    #
    # interpret mets argument
    try:
        f = urlopen(mets)
    except:
        f = open(mets, "rb")
        # physical file: enter METS directory for relative FLocat refs
        os.chdir(os.path.normpath(os.path.dirname(mets)))

    #
    # read in METS
    mets = Mets()
    mets.fulltext_group_name = text_group
    mets.image_group_name = img_group
    mets.fromfile(f)

    #
    # create TEI (from skeleton)
    tei = Tei()

    tei.fill_from_mets(mets, ocr, corresp=add_refs)

    output.write(tei.tostring())


if __name__ == '__main__':
    cli()
