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
        assert(tei.get_main_title() == "Testbuch")
