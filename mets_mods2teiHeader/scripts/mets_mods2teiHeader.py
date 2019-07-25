# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import click
from urllib.request import urlopen

from pkg_resources import resource_filename, Requirement

from mets_mods2teiHeader import Mets
from mets_mods2teiHeader import Tei

@click.command()
@click.argument('mets', required=True)
def cli(mets):
    """ METS: File containing or URL pointing to the METS/MODS XML to be converted """
    
    #
    # interpret mets argument
    try:
        f = urlopen(mets)
    except:
        f = open(mets, "rb")

    #
    # read in METS
    mets = Mets.read(f)

    #
    # create TEI (from skeleton)
    tei = Tei()

    #
    # replace skeleton values by real ones

    # main title
    tei.set_main_title(mets.get_main_title())

    # sub titles
    for sub_title in mets.get_sub_titles():
        tei.add_sub_title(sub_title)

    # authors
    for typ, author in mets.get_authors():
        tei.add_author(author,typ)

    # places
    for place in mets.get_places():
        tei.add_place(place)

    # dates
    for date in mets.get_dates():
        tei.add_date(date)

    # publishers
    for publisher in mets.get_publishers():
        tei.add_publisher(publisher)

    # manuscript edition
    if mets.get_edition():
        tei.add_source_edition(mets.get_edition())

    # digital edition
    if mets.has_digital_origin():
        tei.add_digital_edition(mets.get_digital_origin())

    # hosting institution
    tei.add_hoster(mets.get_owner_digital())

    # availability
    if mets.get_license() != "":
        tei.set_availability("licence", mets.get_license(), mets.get_license_url())
    else:
        tei.set_availability("restricted", mets.get_license(), mets.get_license_url())

    # encoding
    tei.add_encoding_date(mets.get_encoding_date())
    tei.set_encoding_description(mets.get_encoding_description())

    # repository
    if mets.get_owner_manuscript():
        tei.add_repository(mets.get_owner_manuscript())

    # shelf locator
    if mets.get_shelf_locator():
        tei.add_shelfmark(mets.get_shelf_locator())

    # identifiers
    if mets.get_identifiers():
        tei.add_identifiers(mets.get_identifiers())

    # type description
    if mets.get_scripts():
        tei.set_type_desc('\n'.join(script for script in mets.get_scripts()))

    # languages
    for ident_name in mets.get_languages().items():
        tei.add_language(ident_name)

    # extents
    for extent in mets.extents:
        tei.add_extent(extent)

    click.echo(tei.tostring())


if __name__ == '__main__':
    cli()
