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
    Test the creation of an empty Alto instance.
    """
    alto = Alto()
    assert(alto.tree is None)

def test_reading_local_file(datadir):
    """
    Test reading a local ALTO file.
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    assert(alto.tree is not None)

def test_loading_local_file(datadir):
    """
    Test loading a local ALTO file.
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    assert(alto.tree is not None)

def test_text_block_extraction(datadir):
    """
    Test the extraction of text blocks.
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    assert(len(list(alto.get_text_blocks())) == 1)

def test_text_line_extraction(datadir):
    """
    Test the extraction of text lines.
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    text_block = list(alto.get_text_blocks())[0]
    assert(len(list(alto.get_lines_in_text_block(text_block))) == 26)

def test_text_line_text_extraction(datadir):
    """
    Test the extraction of text from text lines.
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
    text_block = list(alto.get_text_blocks())[0]
    text_line = list(alto.get_lines_in_text_block(text_block))[0]
    assert(alto.get_text_in_line(text_line) == "Vorbericht.")

def test_index_assingment(datadir):
    """
    Test the identification of the most likely insertion index.
    """
    with open(datadir.join('test_alto.xml'), 'rb') as f:
        alto = Alto.read(f)
        assert(alto.get_best_insert_index("Vorbericht") == (0,0))

def test_read_path_str(datadir):
    """
    Test Alto.read with file path as a string.
    """
    filepath = str(datadir.join('test_alto.xml'))
    alto = Alto.read(filepath)
    assert alto.tree is not None

def test_write_and_frombytes(datadir):
    """
    Test Alto.write and Alto.frombytes.
    """
    filepath = str(datadir.join('test_alto.xml'))
    from lxml import etree
    tree = etree.parse(filepath)
    alto = Alto()
    alto.tree = tree

    from io import BytesIO
    out = BytesIO()
    alto.write(out)
    content = out.getvalue()
    assert b"<alto" in content

    alto_from_bytes = Alto.frombytes(content)
    assert alto_from_bytes.tree is not None

def test_hyphenation_in_line():
    """
    Test get_text_in_line with HYP element.
    """
    xml = b'''<?xml version="1.0" encoding="UTF-8"?>
    <alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
      <Layout>
        <Page ID="P1">
          <PrintSpace>
            <TextBlock ID="TB1">
              <TextLine ID="TL1">
                <String CONTENT="Vorbe-"/>
                <HYP CONTENT="richt"/>
              </TextLine>
            </TextBlock>
          </PrintSpace>
        </Page>
      </Layout>
    </alto>'''
    alto = Alto.frombytes(xml)
    tb = alto.get_text_blocks()[0]
    line = alto.get_lines_in_text_block(tb)[0]
    assert alto.get_text_in_line(line) == "Vorbe-richt"

def test_best_insert_index_edge_cases():
    """
    Test get_best_insert_index edge cases: label length >= text length, lower=True, distance == 0 match.
    """
    alto = Alto()
    alto.text = "Short"
    assert alto.get_best_insert_index("LongerLabel") == (0, 5)

    alto.text = "Hello World"
    assert alto.get_best_insert_index("hello", lower=True) == (0, 5)

    alto.text = "Some prefix Hello World suffix"
    assert alto.get_best_insert_index("Hello") == (12, 5)

def test_read_non_existent():
    """
    Test Alto.read with non-existent path returns None.
    """
    assert Alto.read("non_existent_file_path_1234.xml") is None

def test_best_insert_index_no_exact_match():
    """
    Test get_best_insert_index when distance is never 0.
    """
    alto = Alto()
    alto.text = "abcdefghij"
    idx, length = alto.get_best_insert_index("xyz")
    assert idx != -1

def test_collect_text_nodes():
    """
    Test collect_text_nodes across single and multiple paragraphs/lines.
    """
    xml = b'''<?xml version="1.0" encoding="UTF-8"?>
    <alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
      <Layout>
        <Page ID="P1">
          <PrintSpace>
            <TextBlock ID="TB1">
              <TextLine ID="TL1"><String CONTENT="Line1"/></TextLine>
              <TextLine ID="TL2"><String CONTENT="Line2"/></TextLine>
            </TextBlock>
            <TextBlock ID="TB2">
              <TextLine ID="TL3"><String CONTENT="Line3"/></TextLine>
              <TextLine ID="TL4"><String CONTENT="Line4"/></TextLine>
            </TextBlock>
          </PrintSpace>
        </Page>
      </Layout>
    </alto>'''
    alto = Alto.frombytes(xml)
    blocks = alto.get_text_blocks()
    lines_b1 = alto.get_lines_in_text_block(blocks[0])
    lines_b2 = alto.get_lines_in_text_block(blocks[1])

    alto.line_index_struct = {
        0: lines_b1[0],
        1: lines_b1[0],
        2: lines_b1[1],
        3: lines_b2[0]
    }

    pars, lines = alto.collect_text_nodes(0, 4)
    assert len(pars) == 1
    assert len(lines) == 3

    xml_single_line_in_tb2 = b'''<?xml version="1.0" encoding="UTF-8"?>
    <alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
      <Layout>
        <Page ID="P1">
          <PrintSpace>
            <TextBlock ID="TB1">
              <TextLine ID="TL1"><String CONTENT="Line1"/></TextLine>
            </TextBlock>
            <TextBlock ID="TB2">
              <TextLine ID="TL3"><String CONTENT="Line3"/></TextLine>
            </TextBlock>
          </PrintSpace>
        </Page>
      </Layout>
    </alto>'''
    alto2 = Alto.frombytes(xml_single_line_in_tb2)
    blocks2 = alto2.get_text_blocks()
    lines_b1_2 = alto2.get_lines_in_text_block(blocks2[0])
    lines_b2_2 = alto2.get_lines_in_text_block(blocks2[1])
    alto2.line_index_struct = {
        0: lines_b1_2[0],
        1: lines_b2_2[0],
    }
    pars2, lines2 = alto2.collect_text_nodes(0, 2)
    assert len(pars2) == 1
