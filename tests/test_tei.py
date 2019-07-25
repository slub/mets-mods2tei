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

    with subtests.test("Check first subtitle"):
        tei.add_sub_title("Untertitel 1")
        assert(tei.subtitles == ["Untertitel 1"])

    with subtests.test("Check further subtitle"):
        tei.add_sub_title("Untertitel 2")
        assert(tei.subtitles == ["Untertitel 1", "Untertitel 2"])

    with subtests.test("Check first author"):
        tei.add_author({'family': 'Mustermann', 'given': 'Max', 'date': '12.10.1956', 'title': 'Dr.'}, "personal")
        assert(tei.authors == ["Mustermann Max Dr."])

    with subtests.test("Check further author (organisation)"):
        tei.add_author({'family': 'Mustermann', 'given': 'Max', 'date': '12.10.1956', 'title': 'Dr.'}, "corporate")
        assert(tei.authors == ["Mustermann Max Dr.", "Mustermann Max 12.10.1956 Dr."])

    with subtests.test("Check first extent"):
        tei.add_extent("32 S.")
        assert(tei.extents == ["32 S."])

    with subtests.test("Check further extent"):
        tei.add_extent("5 Abb.")
        assert(tei.extents == ["32 S.", "5 Abb."])
