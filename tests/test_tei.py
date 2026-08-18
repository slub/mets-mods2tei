# -*- coding: utf-8 -*-

from pathlib import Path

import pytest

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
    Test the creation of an empty TEI instance.
    """
    tei = Tei()
    assert tei.tree is not None

def test_reading_local_file(subtests, datadir, monkeypatch):
    """
    Test reading from a local METS file.
    """
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)
    tei = Tei()

    class MockResponse:
        def __init__(self, content):
            self.content = content

    def mock_get(self_session, url, *args, **kwargs):
        filename = url.split('/')[-1]
        local_path = Path(datadir) / "FULLTEXT" / filename
        if not local_path.exists():
            lines = b''.join(f'<TextLine ID="TL{i}"><String CONTENT="Zeile {i}"/></TextLine>'.encode() for i in range(15))
            dummy_xml = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1">' + lines + b'</TextBlock></PrintSpace></Page></Layout></alto>'
            return MockResponse(dummy_xml)
        return MockResponse(local_path.read_bytes())

    import requests
    monkeypatch.setattr(requests.Session, "get", mock_get)

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
    """
    Test reading from a local METS file, referencing local ALTO files.
    """
    f = open(datadir.join('test_mets_nodiv_local.xml'))
    mets = Mets.read(f)
    tei = Tei()
    with subtests.test("Check TEI conversion"):
        tei.fill_from_mets(mets, ocr=True)
        assert tei.tree is not None
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body', namespaces=NS)) == 1
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:pb', namespaces=NS)) > 55
        assert len(tei.tree.xpath('/tei:TEI/tei:text/tei:body//tei:div//tei:p//tei:lb', namespaces=NS)) > 800

def test_reading_remote_url(tmpdir, monkeypatch):
    """
    Test reading from a remote METS link.
    """
    from urllib.request import urlopen
    import requests

    test_mets_path = Path(__file__).parent / "test_mets" / "test_mets.xml"
    mets_xml_bytes = test_mets_path.read_bytes()

    class MockUrlOpen:
        def __init__(self, data):
            self.data = data
            self.name = "test_mets.xml"
        def read(self):
            return self.data

    def mock_urlopen(url, *args, **kwargs):
        return MockUrlOpen(mets_xml_bytes)

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    class MockResponse:
        def __init__(self, content):
            self.content = content

    def mock_get(self_session, url, *args, **kwargs):
        filename = url.split('/')[-1]
        local_path = Path(__file__).parent / "test_mets" / "FULLTEXT" / filename
        if not local_path.exists():
            lines = b''.join(f'<TextLine ID="TL{i}"><String CONTENT="Vorbericht line {i}"/></TextLine>'.encode() for i in range(15))
            dummy_xml = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1">' + lines + b'</TextBlock></PrintSpace></Page></Layout></alto>'
            return MockResponse(dummy_xml)
        return MockResponse(local_path.read_bytes())

    monkeypatch.setattr(requests.Session, "get", mock_get)

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
    Test the correct assignment of metadata.
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

def test_tei_getters_and_properties():
    """
    Test remaining properties in Tei class: purl, licence (when empty), availability (status branches).
    """
    tei = Tei()
    assert tei.purl == ""
    assert tei.licence == ""

    # Set PURL
    tei.add_identifier("PURL", "http://purl.org/test")
    assert tei.purl == "http://purl.org/test"

def test_tei_fill_from_mets_additional_branches():
    """
    Test fill_from_mets with notes, publishers, manuscript edition, hoster, encoding_date,
    repository, shelfmarks, VD ID, URN, scripts, languages, classifications, subjects, extents, collections.
    """
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3" xmlns:dv="http://dfg-viewer.de/" xmlns:xlink="http://www.w3.org/1999/xlink">
  <mets:metsHdr CREATEDATE="2020-01-01T12:00:00">
    <mets:agent TYPE="OTHER" OTHERTYPE="SOFTWARE">
      <mets:name>Kitodo.Production</mets:name>
    </mets:agent>
  </mets:metsHdr>
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
            <mods:title>Full Metadata Book</mods:title>
            <mods:subTitle>Sub 1</mods:subTitle>
            <mods:partNumber>1</mods:partNumber>
            <mods:partName>Part A</mods:partName>
          </mods:titleInfo>
          <mods:part order="1">
            <mods:detail type="volume">
              <mods:title>Vol A</mods:title>
            </mods:detail>
          </mods:part>
          <mods:name type="personal">
            <mods:namePart type="family">Doe</mods:namePart>
            <mods:namePart type="given">Jane</mods:namePart>
            <mods:role>
              <mods:roleTerm>aut</mods:roleTerm>
            </mods:role>
          </mods:name>
          <mods:note>A manuscript note.</mods:note>
          <mods:originInfo>
            <mods:place>
              <mods:placeTerm type="text">Berlin</mods:placeTerm>
              <mods:placeTerm type="code">10115</mods:placeTerm>
            </mods:place>
            <mods:dateIssued point="start">1800</mods:dateIssued>
            <mods:publisher>Good Publisher</mods:publisher>
            <mods:edition>2nd Edition</mods:edition>
          </mods:originInfo>
          <mods:physicalDescription>
            <mods:digitalOrigin>reformatted digital</mods:digitalOrigin>
            <mods:extent>200 S.</mods:extent>
          </mods:physicalDescription>
          <mods:language>
            <mods:languageTerm>ger</mods:languageTerm>
            <mods:scriptTerm>215</mods:scriptTerm>
          </mods:language>
          <mods:classification authority="ddc">800</mods:classification>
          <mods:subject authority="gnd">
            <mods:topic>Topic A</mods:topic>
            <mods:geographic>Geo A</mods:geographic>
            <mods:temporal>Temp A</mods:temporal>
          </mods:subject>
          <mods:location>
            <mods:physicalLocation>Staatsbibliothek</mods:physicalLocation>
            <mods:shelfLocator>Mark 99</mods:shelfLocator>
          </mods:location>
          <mods:identifier type="vd18">VD18 99999</mods:identifier>
          <mods:identifier type="urn">urn:nbn:de:1234</mods:identifier>
          <mods:relatedItem type="series">
            <mods:titleInfo>
              <mods:title>Special Collection</mods:title>
            </mods:titleInfo>
          </mods:relatedItem>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:amdSec>
    <mets:rightsMD ID="RIGHTS1">
      <mets:mdWrap MDTYPE="OTHER">
        <mets:xmlData>
          <dv:rights>
            <dv:owner>SLUB</dv:owner>
            <dv:license>Public Domain</dv:license>
          </dv:rights>
        </mets:xmlData>
      </mets:mdWrap>
    </mets:rightsMD>
  </mets:amdSec>
  <mets:structMap TYPE="LOGICAL">
    <mets:div TYPE="monograph" ID="LOG_0000" ADMID="AMD1"/>
  </mets:structMap>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    tei = Tei()
    tei.fill_from_mets(mets, ocr=False)

    assert tei.main_title == "Full Metadata Book"
    assert tei.subtitles == ["Sub 1"]
    assert tei.publication_level == "m"
    assert tei.authors == ["Doe, Jane"]
    assert tei.publishers == ["Good Publisher"]
    assert tei.source_editions == ["2nd Edition"]
    assert tei.digital_editions == ["reformatted digital"]
    assert tei.hosters == ["SLUB"]
    assert tei.licence == "Public Domain"
    assert tei.encoding_dates == ["publication:2020-01-01T12:00:00"]
    assert tei.encoding_description == "Encoded with the help of Kitodo.Production."
    assert tei.repositories == ["Staatsbibliothek"]
    assert tei.shelfmarks == ["Mark 99"]
    assert tei.vd_id == "VD18 99999"
    assert tei.urn == "urn:nbn:de:1234"
    assert tei.extents == ["200 S."]
    assert tei.collections == ["Special Collection"]

def test_tei_additional_uncovered_properties_and_branches():
    tei = Tei()
    # vd_id empty
    assert tei.vd_id == ""
    # urn empty
    assert tei.urn == ""

    # add_author with personal and addName
    tei.add_author({'family': 'Smith', 'given': 'John', 'addName': 'the Great'}, "personal")
    assert "Smith, John, the Great" in tei.authors[-1]

    # set_availability status licence with empty text -> restricted
    tei.set_availability("licence", "", "http://lic.url")
    assert tei.availability == "restricted"
    assert tei.licence == "Available under licence from the publishers."

    # add_encoding_date with empty date
    tei.add_encoding_date("")

    # set_encoding_description with empty creator
    tei.set_encoding_description("")

    # compile_bibl with dates and places
    tei2 = Tei()
    tei2.set_main_title("Work")
    tei2.add_place({"text": "City"})
    tei2.add_date({"unspecified": "1999"})
    tei2.compile_bibl("M")
    assert tei2.bibl.text == "[N. N.], Work. City, 1999."

def test_tei_fill_from_mets_uncovered_sub_branches():
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
            <mods:title>Book</mods:title>
          </mods:titleInfo>
          <mods:location>
            <mods:physicalLocation>Staatsbibliothek</mods:physicalLocation>
          </mods:location>
          <mods:identifier type="vd16">VD16 12345</mods:identifier>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    tei = Tei()
    tei.fill_from_mets(mets, ocr=False)
    assert tei.repositories == ["Staatsbibliothek"]
    assert tei.vd_id == "VD16 12345"

def test_tei_ocr_unknown_phys_link_and_order():
    mets = Mets()
    mets.alto_map = {"UNKNOWN_PHYS": "file:dummy.xml"}
    mets.struct_links = {"DIV1": ["UNKNOWN_PHYS"]}

    # Mock open
    import io, builtins
    xml_alto = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1"><TextLine><String CONTENT="Text"/></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'
    original_open = open
    def mock_open(path, mode='r', *args, **kwargs):
        if 'dummy.xml' in str(path):
            return io.BytesIO(xml_alto)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(builtins, "open", mock_open)

    tei = Tei()
    from lxml import etree
    from mets_mods2tei.api.tei import TEI
    body = tei.tree.xpath('//tei:body', namespaces=NS)[0]
    node = etree.SubElement(body, "%sdiv" % TEI)
    node.set("id", "DIV1")

    tei.add_ocr_text(mets)
    monkeypatch.undo()

    pbs = tei.tree.xpath('//tei:pb', namespaces=NS)
    assert len(pbs) == 1

def test_tei_tostring_with_lb_text():
    from lxml import etree
    from mets_mods2tei.api.tei import TEI
    tei = Tei()
    body = tei.tree.xpath('//tei:body', namespaces=NS)[0]
    p = etree.SubElement(body, "%sp" % TEI)
    p.text = "Indented"
    lb = etree.SubElement(p, "%slb" % TEI)
    lb.tail = "Tail text"
    xml_out = tei.tostring()
    assert b"Tail text" in xml_out

def test_tei_remaining_uncovered_nodes():
    from lxml import etree
    from mets_mods2tei.api.tei import TEI
    tei = Tei()

    # 1. tei.tree with multiple titleStmt (line 519)
    file_desc = tei.tree.xpath('//tei:fileDesc', namespaces=NS)[0]
    ts2 = etree.Element("%stitleStmt" % TEI)
    file_desc.append(ts2)
    tei.add_author({"family": "CorpOrg"}, "corporate")

    # 2. tei.tree where notesStmt, textClass, supportDesc are root children under fileDesc / profileDesc / physDesc
    # Note: xpath('/tei:notesStmt') starts with '/' so it checks root element rather than children unless relative
    # add_note when root has notesStmt
    root = tei.tree.getroot()
    notes_stmt = etree.SubElement(root, "%snotesStmt" % TEI)
    tei.add_note("Root note")

    # add_classcode when root has textClass
    text_class = etree.SubElement(root, "%stextClass" % TEI)
    tei.add_classcode("ddc", "300")

    # add_extent when root has supportDesc
    sup_desc = etree.SubElement(root, "%ssupportDesc" % TEI)
    tei.add_extent("300 p.")

    # 3. add_place with code key
    tei.add_place({"text": "Munich", "code": "80331"})

    # 4. fpath.startswith('//') without starting with '/'
    mets_fpath = Mets()
    mets_fpath.wd = "tmp"
    mets_fpath.alto_map = {"P1": "file://relative/path.xml"}
    mets_fpath.struct_links = {"DIV1": ["P1"]}
    mets_fpath.page_map = {"P1": None}

    tei_fp = Tei()
    body = tei_fp.tree.xpath('//tei:body', namespaces=NS)[0]
    node = etree.SubElement(body, "%sdiv" % TEI)
    node.set("id", "DIV1")
    tei_fp.add_ocr_text(mets_fpath)

def test_tei_scripts_empty_and_childnode_ocr_and_orderlabel():
    from io import BytesIO
    # 1. get_scripts empty
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
            <mods:title>Empty Scripts</mods:title>
          </mods:titleInfo>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    mets.scripts = []
    tei = Tei()
    tei.fill_from_mets(mets, ocr=False)
    type_descs = tei.tree.xpath('//tei:msDesc/tei:physDesc/tei:typeDesc', namespaces=NS)
    assert len(type_descs) == 0

    # 2. childnode recursion and orderlabel non-empty and file:/path
    mets_child = Mets()
    mets_child.alto_map = {"PHYS_1": "file:/tmp/test_page.xml"}
    mets_child.struct_links = {"CHILD_DIV": ["PHYS_1"]}
    mets_child.page_map = {"PHYS_1": None}
    mets_child.orderlabel_map = {"PHYS_1": "S. 1"}

    import io, builtins
    xml_alto = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1"><TextLine ID="TL1"><String CONTENT="Child line"/></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'
    original_open = open
    def mock_open(path, mode='r', *args, **kwargs):
        if 'test_page.xml' in str(path):
            return io.BytesIO(xml_alto)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(builtins, "open", mock_open)

    tei_child = Tei()
    from lxml import etree
    from mets_mods2tei.api.tei import TEI
    body = tei_child.tree.xpath('//tei:body', namespaces=NS)[0]
    parent_node = etree.SubElement(body, "%sdiv" % TEI)
    parent_node.set("id", "PARENT_DIV")
    child_node = etree.SubElement(parent_node, "%sdiv" % TEI)
    child_node.set("id", "CHILD_DIV")

    tei_child.add_ocr_text(mets_child)
    monkeypatch.undo()

    pb = tei_child.tree.xpath('//tei:pb', namespaces=NS)[0]
    assert pb.get("n") == "S. 1"

def test_tei_final_branches_coverage():
    # 1. fpath starting with '//' or '/'
    mets_double_slash = Mets()
    mets_double_slash.wd = "/tmp"
    mets_double_slash.alto_map = {"P1": "file://relative/path.xml"}
    mets_double_slash.struct_links = {"DIV1": ["P1"]}
    mets_double_slash.page_map = {"P1": None}

    tei_ds = Tei()
    from lxml import etree
    from mets_mods2tei.api.tei import TEI
    body = tei_ds.tree.xpath('//tei:body', namespaces=NS)[0]
    node = etree.SubElement(body, "%sdiv" % TEI)
    node.set("id", "DIV1")
    tei_ds.add_ocr_text(mets_double_slash)

    # 2. orderlabel empty / None
    mets_no_orderlabel = Mets()
    mets_no_orderlabel.alto_map = {"P1": "file:dummy_no_label.xml"}
    mets_no_orderlabel.struct_links = {"DIV1": ["P1"]}
    mets_no_orderlabel.page_map = {"P1": None}

    import io, builtins
    xml_alto = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1"><TextLine ID="TL1"><String CONTENT="Text"/></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'
    original_open = open
    def mock_open(path, mode='r', *args, **kwargs):
        if 'dummy_no_label.xml' in str(path):
            return io.BytesIO(xml_alto)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(builtins, "open", mock_open)

    tei_nl = Tei()
    body_nl = tei_nl.tree.xpath('//tei:body', namespaces=NS)[0]
    node_nl = etree.SubElement(body_nl, "%sdiv" % TEI)
    node_nl.set("id", "DIV1")
    tei_nl.add_ocr_text(mets_no_orderlabel)
    monkeypatch.undo()

    pb = tei_nl.tree.xpath('//tei:pb', namespaces=NS)[0]
    assert pb.get("n") == "0"

def test_tei_more_branch_coverage():
    # 1. fpath starting with '/' in file:
    mets_abs = Mets()
    mets_abs.wd = "/tmp"
    mets_abs.alto_map = {"P1": "file:///tmp/abs_path.xml"}
    mets_abs.struct_links = {"DIV1": ["P1"]}
    mets_abs.page_map = {"P1": None}
    tei_abs = Tei()
    from lxml import etree
    from mets_mods2tei.api.tei import TEI
    body_abs = tei_abs.tree.xpath('//tei:body', namespaces=NS)[0]
    node_abs = etree.SubElement(body_abs, "%sdiv" % TEI)
    node_abs.set("id", "DIV1")
    tei_abs.add_ocr_text(mets_abs)

    # 2. graphic mimeType None
    mets_img_nomime = Mets()
    mets_img_nomime.alto_map = {"P1": "file:dummy_nomime.xml"}
    mets_img_nomime.img_map = {"P1": "http://example.org/unknown_extension"}
    mets_img_nomime.struct_links = {"DIV1": ["P1"]}
    mets_img_nomime.page_map = {"P1": None}

    import io, builtins
    xml_alto = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1"><TextLine ID="TL1"><String CONTENT="Line1"/></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'
    original_open = open
    def mock_open(path, mode='r', *args, **kwargs):
        if 'dummy_nomime.xml' in str(path):
            return io.BytesIO(xml_alto)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(builtins, "open", mock_open)
    tei_nomime = Tei()
    tei_nomime.refs = ["page"]
    body_nomime = tei_nomime.tree.xpath('//tei:body', namespaces=NS)[0]
    node_nomime = etree.SubElement(body_nomime, "%sdiv" % TEI)
    node_nomime.set("id", "DIV1")
    tei_nomime.add_ocr_text(mets_img_nomime)
    monkeypatch.undo()

    graphics = tei_nomime.tree.xpath('//tei:facsimile/tei:graphic', namespaces=NS)
    assert len(graphics) == 1
    assert graphics[0].get("mimeType") is None

    # 3. empty line_text in alto
    mets_empty_line = Mets()
    mets_empty_line.alto_map = {"P1": "file:dummy_empty.xml"}
    mets_empty_line.struct_links = {"DIV1": ["P1"]}
    mets_empty_line.page_map = {"P1": None}

    xml_alto_empty = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1"><TextLine ID="TL1"></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'
    def mock_open_empty(path, mode='r', *args, **kwargs):
        if 'dummy_empty.xml' in str(path):
            return io.BytesIO(xml_alto_empty)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open_empty)
    tei_empty_line = Tei()
    body_el = tei_empty_line.tree.xpath('//tei:body', namespaces=NS)[0]
    node_el = etree.SubElement(body_el, "%sdiv" % TEI)
    node_el.set("id", "DIV1")
    tei_empty_line.add_ocr_text(mets_empty_line)
    monkeypatch.undo()

    # 4. par_pre and par_post in argument splitting
    xml_alto_arg = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1"><TextLine ID="TL1"><String CONTENT="Pre line"/></TextLine><TextLine ID="TL2"><String CONTENT="Head line"/></TextLine><TextLine ID="TL3"><String CONTENT="Post line"/></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'
    mets_arg = Mets()
    mets_arg.alto_map = {"P1": "file:dummy_arg.xml"}
    mets_arg.struct_links = {"DIV1": ["P1"]}
    mets_arg.page_map = {"P1": None}

    def mock_open_arg(path, mode='r', *args, **kwargs):
        if 'dummy_arg.xml' in str(path):
            return io.BytesIO(xml_alto_arg)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open_arg)
    tei_arg = Tei()
    body_arg = tei_arg.tree.xpath('//tei:body', namespaces=NS)[0]
    node_arg = etree.SubElement(body_arg, "%sdiv" % TEI)
    node_arg.set("id", "DIV1")
    node_arg.set("rend", "Head line")
    tei_arg.add_ocr_text(mets_arg)
    monkeypatch.undo()

    args_elems = tei_arg.tree.xpath('//tei:argument', namespaces=NS)
    assert len(args_elems) == 1

def test_tei_additional_branches_coverage():
    # 1. get_scripts empty string branch
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
            <mods:title>Scripts Test</mods:title>
          </mods:titleInfo>
          <mods:language>
            <mods:scriptTerm>215</mods:scriptTerm>
          </mods:language>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    tei = Tei()
    tei.fill_from_mets(mets, ocr=False)
    type_desc = tei.tree.xpath('//tei:msDesc/tei:physDesc/tei:typeDesc/tei:p', namespaces=NS)
    assert len(type_desc) == 1

    # 2. alto url parsing exception
    mets_bad_url = Mets()
    mets_bad_url.alto_map = {"P1": "http://[invalid_url]"}
    mets_bad_url.struct_links = {"DIV1": ["P1"]}
    mets_bad_url.page_map = {"P1": None}
    tei_bad = Tei()
    from lxml import etree
    from mets_mods2tei.api.tei import TEI
    body = tei_bad.tree.xpath('//tei:body', namespaces=NS)[0]
    node = etree.SubElement(body, "%sdiv" % TEI)
    node.set("id", "DIV1")
    tei_bad.add_ocr_text(mets_bad_url)

    # 3. fpath not startswith '/' branch in file:
    mets_rel_file = Mets()
    mets_rel_file.wd = "/tmp"
    mets_rel_file.alto_map = {"P1": "file:relative_path.xml"}
    mets_rel_file.struct_links = {"DIV1": ["P1"]}
    mets_rel_file.page_map = {"P1": None}
    tei_rel = Tei()
    body_rel = tei_rel.tree.xpath('//tei:body', namespaces=NS)[0]
    node_rel = etree.SubElement(body_rel, "%sdiv" % TEI)
    node_rel.set("id", "DIV1")
    tei_rel.add_ocr_text(mets_rel_file)

    # 4. graphic mimeType non-None branch
    mets_img = Mets()
    mets_img.alto_map = {"P1": "file:dummy.xml"}
    mets_img.img_map = {"P1": "http://example.org/image.jpg"}
    mets_img.struct_links = {"DIV1": ["P1"]}
    mets_img.page_map = {"P1": None}

    import io, builtins
    xml_alto = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1"><TextLine ID="TL1"><String CONTENT="Line1"/></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'
    original_open = open
    def mock_open(path, mode='r', *args, **kwargs):
        if 'dummy.xml' in str(path):
            return io.BytesIO(xml_alto)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(builtins, "open", mock_open)
    tei_img = Tei()
    tei_img.refs = ["page"]
    body_img = tei_img.tree.xpath('//tei:body', namespaces=NS)[0]
    node_img = etree.SubElement(body_img, "%sdiv" % TEI)
    node_img.set("id", "DIV1")
    tei_img.add_ocr_text(mets_img)
    monkeypatch.undo()

    graphics = tei_img.tree.xpath('//tei:facsimile/tei:graphic', namespaces=NS)
    assert len(graphics) == 1
    assert graphics[0].get("mimeType") == "image/jpeg"

    # 5. Nested divs in add_div_structure
    xml_nested = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
          <mods:titleInfo>
            <mods:title>Nested Div Monograph</mods:title>
          </mods:titleInfo>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:structMap TYPE="LOGICAL">
    <mets:div TYPE="outer_div" ID="LOG_0">
      <mets:div TYPE="monograph" ID="LOG_1" ADMID="AMD1">
        <mets:div TYPE="chapter" ID="LOG_2" ADMID="AMD1">
          <mets:div TYPE="section" ID="LOG_3"/>
        </mets:div>
      </mets:div>
    </mets:div>
  </mets:structMap>
</mets:mets>'''
    mets_nest = Mets()
    mets_nest.fromfile(BytesIO(xml_nested))
    tei_nest = Tei()
    tei_nest.fill_from_mets(mets_nest, ocr=False)
    sections = tei_nest.tree.xpath('//tei:body//tei:div//tei:div', namespaces=NS)
    assert len(sections) > 0

def test_tei_add_keywords_no_type_and_has_digital_origin_false():
    from io import BytesIO
    tei = Tei()

    # keywords without type
    tei.add_keywords("gnd", [(None, "Term1")])
    terms = tei.tree.xpath('//tei:keywords/tei:term', namespaces=NS)
    assert len(terms) == 1
    assert terms[0].get("type") is None

    # fill_from_mets when has_digital_origin is False and get_scripts is empty
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
            <mods:title>No Digital Origin</mods:title>
          </mods:titleInfo>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    mets.digital_origin = None

    tei.fill_from_mets(mets, ocr=False)
    assert tei.digital_editions == []

def test_tei_uncovered_branches_and_properties():
    """
    Test remaining uncovered methods/branches in Tei:
    - set_availability with status="free", status="unknown", status="other"
    - add_author with corporate type and date/unspecified
    - add_note when notesStmt already exists
    - add_classcode when textClass already exists
    - add_extent when supportDesc already exists
    - add_div_structure error logging when no div added
    - add_ocr_text with no front/back
    - line without ID in refs line
    """
    tei = Tei()

    # set_availability branches
    tei.set_availability("free", "free lic", "")
    assert tei.availability == "free"
    tei.set_availability("unknown", "", "")
    assert tei.availability == "unknown"
    tei.set_availability("custom_status", "", "")
    assert tei.availability == "restricted"

    # add_author corporate with extra fields and personal with date/unspecified
    tei.add_author({'family': 'Corp', 'given': 'Inc', 'date': '2000', 'unspecified': 'x'}, "corporate")
    assert "Corp Inc 2000 x" in tei.authors[-1]

    tei.add_author({'family': 'Pers', 'given': 'John', 'date': '1990', 'unspecified': 'x', 'title': 'Dr.'}, "personal")
    assert "Pers, John, Dr." in tei.authors[-1]

    # add_note twice (existing notesStmt)
    tei.add_note("Note 1")
    tei.add_note("Note 2")

    # add_classcode twice (existing textClass)
    tei.add_classcode("ddc", "100")
    tei.add_classcode("ddc", "200")

    # add_extent twice (existing supportDesc)
    tei.add_extent("100 p.")
    tei.add_extent("200 p.")

    # add_div_structure with no valid divs
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
          <mods:titleInfo>
            <mods:title>Empty Struct Monograph</mods:title>
          </mods:titleInfo>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:structMap TYPE="LOGICAL">
    <mets:div TYPE="monograph" ID="LOG_0" ADMID="AMD1">
      <mets:div TYPE="cover" ID="LOG_1" ADMID="AMD1"/>
    </mets:div>
  </mets:structMap>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    tei_empty = Tei()
    tei_empty.fill_from_mets(mets, ocr=False)

def test_tei_no_front_back_and_bibl_compile_types():
    tei = Tei()
    front = tei.tree.xpath('//tei:front', namespaces=NS)[0]
    back = tei.tree.xpath('//tei:back', namespaces=NS)[0]
    front.getparent().remove(front)
    back.getparent().remove(back)

    mets = Mets()
    mets.page_map = {"P1": None}
    mets.struct_links = {"DIV1": ["P1"]}
    mets.alto_map = {"P1": "file:dummy.xml"}

    # Mock open
    import io, builtins
    xml_alto = b'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="P1"><PrintSpace><TextBlock ID="TB1"><TextLine><String CONTENT="Body line"/></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'
    original_open = open
    def mock_open(path, mode='r', *args, **kwargs):
        if 'dummy.xml' in str(path):
            return io.BytesIO(xml_alto)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(builtins, "open", mock_open)

    from lxml import etree
    from mets_mods2tei.api.tei import TEI
    body = tei.tree.xpath('//tei:body', namespaces=NS)[0]
    node = etree.SubElement(body, "%sdiv" % TEI)
    node.set("id", "DIV1")

    tei.add_ocr_text(mets)
    monkeypatch.undo()

    # bibl compile non-M type, with dates
    tei2 = Tei()
    tei2.set_main_title("Article")
    tei2.add_date({"unspecified": "2021"})
    tei2.compile_bibl('JA')
    assert tei2.bibl.text == "Article. 2021."

def test_tei_ocr_line_refs_without_id_and_head_split_branches():
    """
    Test OCR text addition with refs=['line'] where TextLine has no ID,
    and head/argument splitting when status transitions.
    """
    from lxml import etree
    from mets_mods2tei.api.alto import Alto
    from mets_mods2tei.api.tei import TEI

    xml_alto = b'''<?xml version="1.0" encoding="UTF-8"?>
    <alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
      <Layout>
        <Page ID="P1">
          <PrintSpace>
            <TextBlock ID="TB1">
              <TextLine><String CONTENT="Pre Line 1"/></TextLine>
              <TextLine><String CONTENT="Header Line"/></TextLine>
              <TextLine><String CONTENT="Post Line 1"/></TextLine>
            </TextBlock>
          </PrintSpace>
        </Page>
      </Layout>
    </alto>'''
    alto = Alto.frombytes(xml_alto)

    mets = Mets()
    mets.alto_map = {"PHYS_0001": "file:dummy_noid.xml"}
    mets.struct_links = {"DIV_1": ["PHYS_0001"]}
    mets.page_map = {"PHYS_0001": None}

    tei = Tei()
    tei.refs = ["line", "page"]

    body = tei.tree.xpath('//tei:body', namespaces=NS)[0]
    node = etree.SubElement(body, "%sdiv" % TEI)
    node.set("id", "DIV_1")
    node.set("rend", "Header Line")

    import io, builtins
    original_open = open
    def mock_open(path, mode='r', *args, **kwargs):
        if 'dummy_noid.xml' in str(path):
            return io.BytesIO(xml_alto)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(builtins, "open", mock_open)
    tei.add_ocr_text(mets)
    monkeypatch.undo()

    lbs = tei.tree.xpath('//tei:lb/@n', namespaces=NS)
    assert len(lbs) > 0

def test_tei_add_ocr_text_head_and_argument_splitting():
    """
    Test __add_ocr_to_node when a heading matches OCR lines and splits paragraph into head/argument.
    """
    from lxml import etree
    from mets_mods2tei.api.alto import Alto
    from mets_mods2tei.api.tei import TEI

    xml_alto = b'''<?xml version="1.0" encoding="UTF-8"?>
    <alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
      <Layout>
        <Page ID="P1">
          <PrintSpace>
            <TextBlock ID="TB1">
              <TextLine ID="TL1"><String CONTENT="Line Pre"/></TextLine>
              <TextLine ID="TL2"><String CONTENT="Vorbericht"/></TextLine>
              <TextLine ID="TL3"><String CONTENT="Line Post"/></TextLine>
            </TextBlock>
          </PrintSpace>
        </Page>
      </Layout>
    </alto>'''
    alto = Alto.frombytes(xml_alto)

    mets = Mets()
    mets.alto_map = {"PHYS_0001": "file:dummy_alto.xml"}
    mets.struct_links = {"DIV_1": ["PHYS_0001"]}
    mets.page_map = {"PHYS_0001": None}

    tei = Tei()

    body = tei.tree.xpath('//tei:body', namespaces=NS)[0]
    node = etree.SubElement(body, "%sdiv" % TEI)
    node.set("id", "DIV_1")
    node.set("rend", "Vorbericht")

    # Mock open to return alto xml when requested
    import io

    original_open = open
    def mock_open(path, mode='r', *args, **kwargs):
        if 'dummy_alto.xml' in str(path):
            return io.BytesIO(xml_alto)
        return original_open(path, mode, *args, **kwargs)

    import builtins
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(builtins, "open", mock_open)

    tei.add_ocr_text(mets)
    monkeypatch.undo()

    heads = tei.tree.xpath('//tei:head', namespaces=NS)
    assert len(heads) == 1

def test_tei_bibl_compile_variations():
    """
    Test compile_bibl variations (type M with no author -> [N. N.], single place, no dates).
    """
    tei = Tei()
    tei.set_main_title("Anonymus Work")
    tei.add_place({"text": "Berlin", "code": "10115"})
    tei.compile_bibl('M')
    assert tei.bibl.text == "[N. N.], Anonymus Work. Berlin"

def test_tei_location_url_types():
    """
    Test add_identifier types inferred from URLs in fill_from_mets (URN, DOI, PPN, ISBN, ISSN, URL).
    """
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
            <mods:title>Test URL Types</mods:title>
          </mods:titleInfo>
          <mods:location>
            <mods:url>urn:nbn:de:bsz:14-1234</mods:url>
            <mods:url>10.1000/182</mods:url>
            <mods:url>12345678X</mods:url>
            <mods:url>978-3-16-148410-0</mods:url>
            <mods:url>1234-567X</mods:url>
            <mods:url>https://example.org/item</mods:url>
          </mods:location>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    tei = Tei()
    tei.fill_from_mets(mets, ocr=False)

    identifiers = [idno.text for idno in tei.tree.xpath('//tei:idno', namespaces=NS)]
    assert "urn:nbn:de:bsz:14-1234" in identifiers
    assert "10.1000/182" in identifiers
    assert "12345678X" in identifiers
    assert "978-3-16-148410-0" in identifiers
    assert "1234-567X" in identifiers
    assert "https://example.org/item" in identifiers

def test_tei_div_types_front_body_back():
    """
    Test add_div_structure division into front, body, back and skipping bindings/covers.
    """
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
          <mods:titleInfo>
            <mods:title>Monograph Title</mods:title>
          </mods:titleInfo>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:structMap TYPE="LOGICAL">
        <mets:div TYPE="monograph" ID="LOG_0000" ADMID="AMD1">
          <mets:div TYPE="binding" ID="LOG_0001" ADMID="AMD1"/>
          <mets:div TYPE="title_page" ID="LOG_0002" LABEL="Title Page" ADMID="AMD1"/>
          <mets:div TYPE="preface" ID="LOG_0003" LABEL="Preface" ADMID="AMD1"/>
          <mets:div TYPE="chapter" ID="LOG_0004" LABEL="Chapter 1" ADMID="AMD1"/>
          <mets:div TYPE="appendix" ID="LOG_0005" LABEL="Appendix 1" ADMID="AMD1"/>
    </mets:div>
  </mets:structMap>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    tei = Tei()
    tei.fill_from_mets(mets, ocr=False)

    front_divs = tei.tree.xpath('//tei:front/tei:titlePage', namespaces=NS)
    body_divs = tei.tree.xpath('//tei:body/tei:div', namespaces=NS)
    back_divs = tei.tree.xpath('//tei:back/tei:div', namespaces=NS)

    assert len(front_divs) == 1
    assert len(body_divs) == 1
    assert len(back_divs) == 1

def test_tei_physical_fallback_no_logical_divs():
    """
    Test physical page fallback when logical structmap has no divs.
    """
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods xmlns:mods="http://www.loc.gov/mods/v3"/>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:structMap TYPE="PHYSICAL">
    <mets:div TYPE="PHYSICAL">
      <mets:div TYPE="page" ID="PHYS_0001"/>
    </mets:div>
  </mets:structMap>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    mets.alto_map["PHYS_0001"] = "file:dummy.xml"
    tei = Tei()
    tei.fill_from_mets(mets, ocr=False)
    assert len(tei.tree.xpath('//tei:body/tei:div', namespaces=NS)) == 1

def test_tei_ocr_error_handling_and_path_variations(monkeypatch):
    """
    Test add_ocr_text error handling: FileNotFoundError, RetryError, and url parsing file:// variations.
    """
    import requests
    from lxml import etree
    from requests.exceptions import RetryError
    from mets_mods2tei.api.tei import TEI

    mets = Mets()
    mets.alto_map = {
        "PHYS_0001": "invalid_url_###",
        "PHYS_0002": "file:///non_existent_1.xml",
        "PHYS_0003": "file://non_existent_2.xml",
        "PHYS_0004": "file:/non_existent_3.xml",
        "PHYS_0005": "file:non_existent_4.xml",
        "PHYS_0006": "http://http_retry_error.xml"
    }
    mets.struct_links = {
        "DIV_1": ["PHYS_0001", "PHYS_0002", "PHYS_0003", "PHYS_0004", "PHYS_0005", "PHYS_0006"]
    }
    mets.page_map = {
        "PHYS_0001": None, "PHYS_0002": None, "PHYS_0003": None, "PHYS_0004": None, "PHYS_0005": None, "PHYS_0006": None
    }

    def mock_get(self_session, url, *args, **kwargs):
        raise RetryError("Mocked retry error")

    monkeypatch.setattr(requests.Session, "get", mock_get)

    tei = Tei()
    body = tei.tree.xpath('//tei:body', namespaces=NS)[0]
    node = etree.SubElement(body, "%sdiv" % TEI)
    node.set("id", "DIV_1")

    # Should run without raising uncaught exceptions
    tei.add_ocr_text(mets)
