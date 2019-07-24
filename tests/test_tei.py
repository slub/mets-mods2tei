# -*- coding: utf-8 -*-

from mets_mods2teiHeader import Tei

def test_constructor():
    '''
    Test the creation of an empty Tei instance
    '''
    tei = Tei()
    assert(tei.tree is not None)

def test_data_assignment(subtests):
    '''
    Test the correct assignment of meta data
    '''
    tei = Tei()

    with subtests.test("Check main title"):
        tei.set_main_title("Testbuch")
        assert(tei.main_title == "Testbuch")

    with subtests.test("Check extent(s)"):
        tei.add_extent("32 S.")
        tei.add_extent("5 Abb.")
        assert(tei.extents == ["32 S.", "5 Abb."])
