# -*- coding: utf-8 -*-

from mets_mods2tei import Iso15924

def test_constructor():
    '''
    Test the creation of an Iso15924 instance
    '''
    iso = Iso15924()
    assert(iso.map is not {})

def test_existing_script():
    '''
    Test requesting the script name for an existing code
    '''
    iso = Iso15924()
    assert(iso.get('Latf') == "Latin (Fraktur variant)")

def test_non_existing_script():
    '''
    Test requesting the script name for a non-existing code
    '''
    iso = Iso15924()
    assert(iso.get('kkk') == "Unknown")
