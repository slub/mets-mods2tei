# -*- coding: utf-8 -*-

import os
import pytest
import warnings

# the import of dir_util introduces a deprecation warning
# we can't do much about it
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from distutils import dir_util

from mets_mods2tei import Alto

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
    Test the creation of an empty Alto instance
    '''
    alto = Alto()
    assert(alto.tree is None)

def test_reading_local_file(datadir):
    '''
    Test reading a local alto file
    '''
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    assert(alto.tree is not None)

def test_loading_local_file(datadir):
    '''
    Test loading a local alto file
    '''
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    assert(alto.tree is not None)

def test_text_block_extraction(datadir):
    '''
    Test the extraction of text blocks
    '''
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    assert(len(list(alto.get_text_blocks())) == 1)

def test_text_line_extraction(datadir):
    '''
    Test the extraction of text lines
    '''
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    text_block = list(alto.get_text_blocks())[0]
    assert(len(list(alto.get_lines_in_text_block(text_block))) == 26)

def test_text_line_text_extraction(datadir):
    '''
    Test the extraction of text from text lines
    '''
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    text_block = list(alto.get_text_blocks())[0]
    text_line = list(alto.get_lines_in_text_block(text_block))[0]
    assert(alto.get_text_in_line(text_line) == "Vorbericht.")
