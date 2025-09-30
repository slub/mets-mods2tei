# -*- coding: utf-8 -*-

import os
import pytest
import shutil

from mets_mods2tei import Tei
from mets_mods2tei import Mets

NS = {
    'tei': 'http://www.tei-c.org/ns/1.0'
}

@pytest.fixture
def datadir(tmpdir, request):
    """
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    """
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        shutil.copytree(test_dir, str(tmpdir), dirs_exist_ok=True)

    return tmpdir

def test_constructor():
    """
    Test the creation of an empty Tei instance
    """
    tei = Tei()
    assert tei.tree is not None

def test_reading_local_file(subtests, datadir):
    """
    Test reading from a local mets file
    """
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)
    tei = Tei()
    with subtests.test("Check TEI conversion"):
        tei.fill_from_mets(mets, ocr=False)
        assert tei.tree is not None
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body', namespaces=NS)) == 1
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:pb', namespaces=NS)) == 0
    with subtests.test("Check TEI conversion with OCR"):
        tei.add_ocr_text(mets)
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:pb', namespaces=NS)) > 700
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:p//tei:lb', namespaces=NS)) > 8000

def test_reading_local_file_local_ocr(subtests, datadir):
    '''
    Test reading from a local mets file, referencing local alto files
    '''
    f = open(datadir.join('test_mets_nodiv_local.xml'))
    mets = Mets.read(f)
    tei = Tei()
    with subtests.test("Check TEI conversion"):
        tei.fill_from_mets(mets, ocr=True)
        assert tei.tree is not None
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body', namespaces=NS)) == 1
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:pb', namespaces=NS)) > 55
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:p//tei:lb', namespaces=NS)) > 800

def test_reading_remote_url(tmpdir):
    '''
    Test reading from a remote mets link
    '''
    from urllib.request import urlopen
    mets = Mets()
    mets.fromfile(urlopen("https://digital.slub-dresden.de/oai/?verb=GetRecord&metadataPrefix=mets"
                          "&identifier=oai:de:slub-dresden:db:id-453779263"))
    tei = Tei()
    tei.fill_from_mets(mets, ocr=True, refs=["page", "line"])
    assert tei.tree is not None
    assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body', namespaces=NS)) == 1
    # check pages
    assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:front//tei:div//tei:pb', namespaces=NS)) > 1
    assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:front/tei:titlePage', namespaces=NS)) == 1
    assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:back//tei:div//tei:pb', namespaces=NS)) > 1
    assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:pb', namespaces=NS)) >= 80
    # check pb/@corresp refs
    assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:pb/@corresp', namespaces=NS)) >= 80
    # check idrefs for facsimlie/graphic/@id | pb/@n links:
    assert len(tei.tree.xpath('/tei:TEI/tei:facsimile/tei:graphic[concat("#",@id)=/tei:TEI/tei:text/tei:body//tei:div//tei:pb/@facs]', namespaces=NS)) >= 80
    # check lines
    assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:p//tei:lb', namespaces=NS)) > 800
    # check lb/@n refs
    assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:p//tei:lb/@n', namespaces=NS)) > 800

def test_string_dumping():
    tei = Tei()
    assert tei.tostring().startswith(b"<")

def test_data_assignment(subtests):
    """
    Test the correct assignment of meta data
    """
    tei = Tei()

    with subtests.test("Check main title"):
        tei.set_main_title("Testbuch")
        assert tei.main_title == "Testbuch"

    with subtests.test("Check first subtitle"):
        tei.add_sub_title("Untertitel 1")
        assert tei.subtitles == ["Untertitel 1"]

    with subtests.test("Check further subtitle"):
        tei.add_sub_title("Untertitel 2")
        assert tei.subtitles == ["Untertitel 1", "Untertitel 2"]

    with subtests.test("Check publication level"):
        tei.init_biblFull()
        tei.set_publication_level("m")
        assert tei.publication_level == "m"

    with subtests.test("Check first author"):
        tei.add_author({'family': 'Mustermann', 'given': 'Max', 'date': '12.10.1956', 'title': 'Dr.'}, "personal")
        assert tei.authors == ["Mustermann, Max, Dr."]

    with subtests.test("Check further author (organisation)"):
        tei.add_author({'family': 'Mustermann', 'given': 'Max', 'date': '12.10.1956', 'title': 'Dr.'}, "corporate")
        assert tei.authors == ["Mustermann, Max, Dr.", "Mustermann Max 12.10.1956 Dr."]

    with subtests.test("Check date(s)"):
        tei.add_date({"from": "01.01.1823", "to": "25.01.1823"})
        assert tei.dates == ["01.01.1823", "25.01.1823"]

    with subtests.test("Check place(s)"):
        tei.add_place({"text": "Dresden", "code": "01277"})
        assert tei.places == ["01277:Dresden"]
        tei.add_place({"text": "Leipzig", "code": "04347"})
        assert tei.places == ["01277:Dresden", "04347:Leipzig"]

    with subtests.test("Check publisher"):
        tei.add_publisher("Joachim Mustermann")
        assert tei.publishers == ["Joachim Mustermann"]

    with subtests.test("Check source edition"):
        tei.add_source_edition("18. Aufl.")
        assert tei.source_editions == ["18. Aufl."]

    with subtests.test("Check digital edition"):
        tei.add_digital_edition("reformatted digital")
        assert tei.digital_editions == ["reformatted digital"]

    with subtests.test("Check digital publisher"):
        tei.add_hoster("SLUB")
        assert tei.hosters == ["SLUB"]

    with subtests.test("Check availability"):
        tei.set_availability("licence", "Public domain", "")
        assert tei.availability == "licenced"
        tei.set_availability("free", "", "")
        assert tei.availability == "free"
        tei.set_availability("unknown", "", "")
        assert tei.availability == "unknown"
        tei.set_availability("foo", "", "")
        assert tei.availability == "restricted"

    with subtests.test("Check licence"):
        tei.set_availability("licence", "Public domain", "")
        assert tei.licence == "Public domain"

    with subtests.test("Check encoding date"):
        tei.add_encoding_date("25.01.2020")
        assert tei.encoding_dates == ["publication:25.01.2020"]

    with subtests.test("Check encoding description"):
        tei.set_encoding_description("Kitodo.Production")
        assert tei.encoding_description == "Encoded with the help of Kitodo.Production."

    with subtests.test("Check repositories"):
        tei.add_repository("Kitodo.Production")
        tei.add_repository("Saxonica")
        assert tei.repositories == ["Kitodo.Production", "Saxonica"]

    with subtests.test("Check shelfmarks"):
        tei.add_identifier("shelfmark", "Foo 25")
        tei.add_identifier("shelfmark", "HAL 9000")
        assert tei.shelfmarks == ["Foo 25", "HAL 9000"]

    with subtests.test("Check VD ID"):
        tei.add_identifier("VD", "VD18 11413883")
        assert tei.vd_id == "VD18 11413883"

    with subtests.test("Check URN"):
        tei.add_identifier("URN", "urn:nbn:de:bsz:14-db-id4971666239")
        assert tei.urn == "urn:nbn:de:bsz:14-db-id4971666239"

    with subtests.test("Check first extent"):
        tei.add_extent("32 S.")
        assert tei.extents == ["32 S."]

    with subtests.test("Check further extent"):
        tei.add_extent("5 Abb.")
        assert tei.extents == ["32 S.", "5 Abb."]

    with subtests.test("Check collections"):
        tei.add_collection("LDP")
        assert tei.collections == ["LDP"]

    with subtests.test("Check bibl"):
        tei.compile_bibl('M')
        assert tei.bibl.text == "Mustermann, Max, Dr.; Mustermann Max 12.10.1956 Dr.: Testbuch. Dresden u. a., 01.01.1823."
