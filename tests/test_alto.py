# -*- coding: utf-8 -*-

from pathlib import Path

import pytest

from mets_mods2tei import Alto

@pytest.fixture
def datadir(tmpdir, request):
    """
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    """
    src = Path(request.module.__file__).with_suffix('')
    if src.is_dir():
        for src_path in src.glob('**/*'):
            if src_path.is_file():
                dest_path = Path(str(tmpdir)) / src_path.relative_to(src)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_bytes(src_path.read_bytes())
    return tmpdir

def test_constructor():
    """
    Test the creation of an empty Alto instance
    """
    alto = Alto()
    assert(alto.tree is None)

def test_reading_local_file(datadir):
    """
    Test reading a local alto file
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    assert(alto.tree is not None)

def test_loading_local_file(datadir):
    """
    Test loading a local alto file
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    assert(alto.tree is not None)

def test_text_block_extraction(datadir):
    """
    Test the extraction of text blocks
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    assert(len(list(alto.get_text_blocks())) == 1)

def test_text_line_extraction(datadir):
    """
    Test the extraction of text lines
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    text_block = list(alto.get_text_blocks())[0]
    assert(len(list(alto.get_lines_in_text_block(text_block))) == 26)

def test_text_line_text_extraction(datadir):
    """
    Test the extraction of text from text lines
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    text_block = list(alto.get_text_blocks())[0]
    text_line = list(alto.get_lines_in_text_block(text_block))[0]
    assert(alto.get_text_in_line(text_line) == "Vorbericht.")

def test_index_assingment(datadir):
    """
    Test the identifcation of the most likely insertion index
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
        assert(alto.get_best_insert_index("Vorbericht") == (0,0))
