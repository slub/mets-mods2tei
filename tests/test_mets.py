# -*- coding: utf-8 -*-

import os
import pytest
import warnings

# the import of dir_util introduces a deprecation warning
# we can't do much about it
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from distutils import dir_util

from mets_mods2tei import Mets

@pytest.fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir

def test_constructor():
    '''
    Test the creation of an empty Mets instance
    '''
    mets = Mets()
    assert(mets.mets is None)

def test_reading_local_file(datadir):
    '''
    Test reading a local mets file
    '''
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)
    assert(mets.mets is not None)

def test_loading_local_file(datadir):
    '''
    Test loading a local mets file
    '''
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.from_file(f)
    assert(mets.mets is not None)

def test_intermediate_file_loading(datadir):
    '''
    Test loading a local mets file
    '''
    f = open(datadir.join('test_mets.xml'))
    mets = Mets()
    mets.fromfile(f)
    assert(mets.mets is not None)

def test_fulltext_group_name(subtests, datadir):
    '''
    Test getting and setting the full text group name
    '''
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)

    with subtests.test("Check getter"):
        assert(mets.fulltext_group_name == "FULLTEXT")

    with subtests.test("Check setter"):
        mets.fulltext_group_name = "TEXT"
        assert(mets.fulltext_group_name == "TEXT")

def test_mappings(subtests, datadir):
    '''
    Test the correct interpretation of the structural linking
    '''
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)

    with subtests.test("Check struct links"):
        assert(mets.get_struct_links('LOG_0000')[0] == "PHYS_0001")

    with subtests.test("Check ALTO linkage"):
        assert(mets.get_alto('PHYS_0005') == 'https://digital.slub-dresden.de/data/kitodo/LoskGesc_497166623/LoskGesc_497166623_ocr/00000005.xml')

    with subtests.test("Check IMG linkage"):
        assert(mets.get_img('PHYS_0005') == 'https://digital.slub-dresden.de/data/kitodo/LoskGesc_497166623/LoskGesc_497166623_tif/jpegs/00000005.tif.medium.jpg')

def test_data_assignment(subtests, datadir):
    '''
    Test the correct assignment of meta data
    '''
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)

    with subtests.test("Check main title"):
        assert(mets.get_main_title() == "Geschichte der Mission der evangelischen Brüder unter den Indianern in Nordamerika")

    with subtests.test("Check author(s)"):
        assert(mets.get_authors() == [('personal', {'family': 'Loskiel', 'given': 'Georg Heinrich'})])

    with subtests.test("Check subtitle(s)"):
        assert(mets.get_sub_titles() == ['ein Führer für Reisende; mit Kartenbeilagen und Illustrationen in Holzschnitt'])

    with subtests.test("Check place(s)"):
        assert(mets.get_places() == [{'text': 'Barby'}, {'text': 'Leipzig'}])

    with subtests.test("Check manuscript edition"):
        assert(mets.get_edition() == '3. Aufl.')

    with subtests.test("Check manuscript language(s)"):
        assert(mets.get_languages() == {'ger': 'Deutsch'})

    with subtests.test("Check manuscript script(s)"):
        assert(mets.get_scripts() == ['Latin (Fraktur variant)'])

    with subtests.test("Check manuscript digital origin"):
        assert(mets.get_digital_origin() == 'reformatted digital')

    with subtests.test("Check manuscript extent"):
        assert(mets.extents == ['[8] Bl., 783 S., [1] Bl.'])

    with subtests.test("Check collections"):
        assert(mets.collections == ['Drucke des 18. Jahrhunderts', 'Saxonica'])

    with subtests.test("Check publication date(s)"):
        assert(mets.get_dates() == {'unspecified': '1789'})

    with subtests.test("Check encoding date"):
        assert(mets.get_encoding_date() == '2018-01-18T13:17:11')

    with subtests.test("Check shelf locator(s)"):
        assert(mets.get_shelf_locators() == ['Hist.Amer.1497'])

    with subtests.test("Check URN"):
        assert "urn" in mets.get_identifiers()
        assert mets.get_identifiers()["urn"] == 'urn:nbn:de:bsz:14-db-id4971666239'

    with subtests.test("Check VD ID"):
        assert "vd18" in mets.get_identifiers()
        assert mets.get_identifiers()["vd18"] == 'VD18 11413883'
