# -*- coding: utf-8 -*-

from mets_mods2teiHeader import Tei

def test_constructor():
    '''
    Test the creation of an empty Tei instance
    '''
    tei = Tei()
    assert(tei.tree is not None)

def test_string_dumping():
    tei = Tei()
    assert(tei.tostring().startswith(b"<"))

def test_data_assignment(subtests):
    '''
    Test the correct assignment of meta data
    '''
    tei = Tei()

    with subtests.test("Check main title"):
        tei.set_main_title("Testbuch")
        assert(tei.main_title == "Testbuch")

    with subtests.test("Check publication level"):
        tei.set_publication_level("m")
        assert(tei.publication_level == "m")

    with subtests.test("Check first subtitle"):
        tei.add_sub_title("Untertitel 1")
        assert(tei.subtitles == ["Untertitel 1"])

    with subtests.test("Check further subtitle"):
        tei.add_sub_title("Untertitel 2")
        assert(tei.subtitles == ["Untertitel 1", "Untertitel 2"])

    with subtests.test("Check first author"):
        tei.add_author({'family': 'Mustermann', 'given': 'Max', 'date': '12.10.1956', 'title': 'Dr.'}, "personal")
        assert(tei.authors == ["Mustermann, Max, Dr."])

    with subtests.test("Check further author (organisation)"):
        tei.add_author({'family': 'Mustermann', 'given': 'Max', 'date': '12.10.1956', 'title': 'Dr.'}, "corporate")
        assert(tei.authors == ["Mustermann, Max, Dr.", "Mustermann Max 12.10.1956 Dr."])

    with subtests.test("Check date(s)"):
        tei.add_date({"from": "01.01.1823", "to": "25.01.1823"})
        assert(tei.dates == ["01.01.1823", "25.01.1823"])

    with subtests.test("Check place(s)"):
        tei.add_place({"text": "Dresden", "code": "01277"})
        assert(tei.places == ["01277:Dresden"])

    with subtests.test("Check publisher"):
        tei.add_publisher("Joachim Mustermann")
        assert(tei.publishers == ["Joachim Mustermann"])

    with subtests.test("Check source edition"):
        tei.add_source_edition("18. Aufl.")
        assert(tei.source_editions == ["18. Aufl."])

    with subtests.test("Check digital edition"):
        tei.add_digital_edition("reformatted digital")
        assert(tei.digital_editions == ["reformatted digital"])

    with subtests.test("Check digital publisher"):
        tei.add_hoster("SLUB")
        assert(tei.hosters == ["SLUB"])

    with subtests.test("Check encoding date"):
        tei.add_encoding_date("25.01.2020")
        assert(tei.encoding_dates == ["publication:25.01.2020"])

    with subtests.test("Check first extent"):
        tei.add_extent("32 S.")
        assert(tei.extents == ["32 S."])

    with subtests.test("Check further extent"):
        tei.add_extent("5 Abb.")
        assert(tei.extents == ["32 S.", "5 Abb."])

    with subtests.test("Check collections"):
        tei.add_collection("LDP")
        assert(tei.collections == ["LDP"])

    with subtests.test("Check bibl"):
        tei.compile_bibl()
        assert(tei.bibl.text == "Mustermann, Max, Dr.; Mustermann Max 12.10.1956 Dr.: Testbuch. Dresden, 01.01.1823.")
