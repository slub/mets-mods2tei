# -*- coding: utf-8 -*-

from pathlib import Path

import pytest

from mets_mods2tei import Mets

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
    Test the creation of an empty METS instance.
    """
    mets = Mets()
    assert mets.mets is None

def test_reading_local_file(datadir):
    """
    Test reading a local METS file.
    """
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)
    assert mets.mets is not None

def test_loading_local_file(datadir):
    """
    Test loading a local METS file.
    """
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.from_file(f)
    assert mets.mets is not None

def test_intermediate_file_loading(datadir):
    """
    Test loading a local METS file.
    """
    f = open(datadir.join('test_mets.xml'))
    mets = Mets()
    mets.fromfile(f)
    assert mets.mets is not None

def test_fulltext_group_name(subtests, datadir):
    """
    Test getting and setting the full text group name.
    """
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)

    with subtests.test("Check getter"):
        assert mets.fulltext_group_name == "FULLTEXT"

    with subtests.test("Check setter"):
        mets.fulltext_group_name = "TEXT"
        assert mets.fulltext_group_name == "TEXT"

def test_mappings(subtests, datadir):
    """
    Test the correct interpretation of the structural linking.
    """
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)

    with subtests.test("Check struct links"):
        assert mets.get_struct_links('LOG_0000')[0] == "PHYS_0001"

    with subtests.test("Check ALTO linkage"):
        assert mets.get_alto('PHYS_0005') == 'https://digital.slub-dresden.de/data/kitodo/LoskGesc_497166623/LoskGesc_497166623_ocr/00000005.xml'

    with subtests.test("Check IMG linkage"):
        assert mets.get_img('PHYS_0005') == 'https://digital.slub-dresden.de/data/kitodo/LoskGesc_497166623/LoskGesc_497166623_tif/jpegs/00000005.tif.medium.jpg'

def test_data_assignment(subtests, datadir):
    """
    Test the correct assignment of metadata.
    """
    f = open(datadir.join('test_mets.xml'))
    mets = Mets.read(f)

    with subtests.test("Check main title"):
        assert mets.get_main_title() == "Geschichte der Mission der evangelischen Brüder unter den Indianern in Nordamerika"

    with subtests.test("Check author(s)"):
        assert mets.get_authors() == [('personal', {'family': 'Loskiel', 'given': 'Georg Heinrich'})]

    with subtests.test("Check subtitle(s)"):
        assert mets.get_sub_titles() == ['ein Führer für Reisende; mit Kartenbeilagen und Illustrationen in Holzschnitt']

    with subtests.test("Check place(s)"):
        assert mets.get_places() == [{'text': 'Barby'}, {'text': 'Leipzig'}]

    with subtests.test("Check manuscript edition"):
        assert mets.get_edition() == '3. Aufl.'

    with subtests.test("Check manuscript language(s)"):
        assert mets.get_languages() == {'ger': 'Deutsch'}

    with subtests.test("Check manuscript script(s)"):
        assert mets.get_scripts() == ['Latin (Fraktur variant)']

    with subtests.test("Check manuscript digital origin"):
        assert mets.get_digital_origin() == 'reformatted digital'

    with subtests.test("Check manuscript extent"):
        assert mets.extents == ['[8] Bl., 783 S., [1] Bl.']

    with subtests.test("Check collections"):
        assert mets.collections == ['Drucke des 18. Jahrhunderts', 'Saxonica']

    with subtests.test("Check publication date(s)"):
        assert mets.get_dates() == {'unspecified': '1789'}

    with subtests.test("Check encoding date"):
        assert mets.get_encoding_date() == '2018-01-18T13:17:11'

    with subtests.test("Check shelf locator(s)"):
        assert mets.get_shelf_locators() == ['Hist.Amer.1497']

    with subtests.test("Check URN"):
        assert "urn" in mets.get_identifiers()
        assert mets.get_identifiers()["urn"] == 'urn:nbn:de:bsz:14-db-id4971666239'

    with subtests.test("Check VD ID"):
        assert "vd18" in mets.get_identifiers()
        assert mets.get_identifiers()["vd18"] == 'VD18 11413883'

def test_mappings_only_phys(subtests, datadir):
    """
    Test the correct interpretation of the structural linking.
    """
    f = open(datadir.join('test_mets_nodiv.xml'))
    mets = Mets()
    mets.image_group_name = 'ORIGINAL'
    mets.fromfile(f)

    with subtests.test("Check struct links"):
        assert mets.get_struct_links('LOG_0000')[0] == "PHYS_0001"
        assert mets.get_struct_links('LOG_0000')[1] == "PHYS_0002"

    with subtests.test("Check ALTO linkage"):
        assert mets.get_alto('PHYS_0005') == 'https://digital.slub-dresden.de/data/kitodo/BurgAbha_1852685697/BurgAbha_1852685697_ocr/00000005.xml'

    with subtests.test("Check IMG linkage"):
        assert mets.get_img('PHYS_0005') == 'https://digital.slub-dresden.de/data/kitodo/BurgAbha_1852685697/BurgAbha_1852685697_tif/jpegs/00000005.tif.original.jpg'

def test_mappings_only_phys_local(subtests, datadir):
    """
    Test the correct interpretation of local file references.
    """
    f = open(datadir.join('test_mets_nodiv_local.xml'))
    mets = Mets()
    mets.image_group_name = 'ORIGINAL'
    mets.fromfile(f)

    with subtests.test("Check ALTO linkage"):
        assert mets.get_alto('PHYS_0005') == 'FULLTEXT/uuid-bea1c083-9bde-412a-beca-8a85e99a1a71.xml'

def test_mets_read_variants(datadir):
    """
    Test Mets.read with string path, existing vs non-existing file.
    """
    filepath = str(datadir.join('test_mets.xml'))
    m1 = Mets.read(filepath)
    assert m1.mets is not None

    m2 = Mets.read("non_existent_mets_file.xml")
    assert m2 is None

def test_iso15924_unknown():
    from mets_mods2tei.api.mets import Iso15924
    iso = Iso15924()
    assert iso.get("XXXX") == "Unknown"

def test_mets_div_types_and_metadata():
    """
    Test Mets handling of various div types (bachelor_thesis, contained_work, article, periodical, lecture),
    titleInfo types, parts, roles, notes, dv:rightsMD, locations, subjects, classifications, etc.
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
          <mods:titleInfo type="uniform">
            <mods:title>Uniform Title</mods:title>
            <mods:subTitle>Subtitle Uniform</mods:subTitle>
            <mods:partNumber>Vol. 1</mods:partNumber>
            <mods:partName>Part Name</mods:partName>
          </mods:titleInfo>
          <mods:part order="1">
            <mods:detail type="volume">
              <mods:number>1</mods:number>
              <mods:caption>Cap</mods:caption>
              <mods:title>Vol Title</mods:title>
            </mods:detail>
          </mods:part>
          <mods:name type="personal">
            <mods:namePart type="family">EditorFam</mods:namePart>
            <mods:namePart type="given">EditorGiv</mods:namePart>
            <mods:role>
              <mods:roleTerm>edt</mods:roleTerm>
            </mods:role>
          </mods:name>
          <mods:name type="corporate">
            <mods:namePart>CorpAuthor</mods:namePart>
            <mods:role>
              <mods:roleTerm>aut</mods:roleTerm>
            </mods:role>
          </mods:name>
          <mods:note>Note 1</mods:note>
          <mods:language>
            <mods:languageTerm>invalidlangcode</mods:languageTerm>
            <mods:scriptTerm>215</mods:scriptTerm>
          </mods:language>
          <mods:classification authority="ddc">800</mods:classification>
          <mods:subject authority="gnd">
            <mods:topic>Topic1</mods:topic>
            <mods:geographic>Geo1</mods:geographic>
            <mods:temporal>Temp1</mods:temporal>
          </mods:subject>
          <mods:location>
            <mods:physicalLocation>Library</mods:physicalLocation>
            <mods:url>http://example.org</mods:url>
            <mods:shelfLocator>Mark 123</mods:shelfLocator>
          </mods:location>
          <mods:relatedItem type="series">
            <mods:titleInfo>
              <mods:title>Series Title</mods:title>
            </mods:titleInfo>
          </mods:relatedItem>
          <mods:accessCondition type="use and reproduction" xlink:href="http://license.url">Lic Text</mods:accessCondition>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:amdSec>
    <mets:rightsMD ID="RIGHTS1">
      <mets:mdWrap MDTYPE="OTHER">
        <mets:xmlData>
          <dv:rights>
            <dv:owner>SLUB Dresden</dv:owner>
            <dv:license>Public Domain</dv:license>
          </dv:rights>
        </mets:xmlData>
      </mets:mdWrap>
    </mets:rightsMD>
  </mets:amdSec>
  <mets:structMap TYPE="LOGICAL">
    <mets:div TYPE="bachelor_thesis" LABEL="Thesis Label"/>
  </mets:structMap>
  <mets:structMap TYPE="PHYSICAL">
    <mets:div TYPE="PHYSICAL">
      <mets:div TYPE="page" ID="PHYS_0001" ORDER="1" ORDERLABEL="Page 1"/>
    </mets:div>
  </mets:structMap>
</mets:mets>'''

    mets = Mets()
    mets.fromfile(BytesIO(xml_content))

    assert mets.get_main_title() == "Uniform Title"
    assert mets.get_sub_titles() == ["Subtitle Uniform"]
    assert mets.get_part_titles() == {"Vol. 1": "Part Name"}
    assert mets.get_volume_titles() == {("1", "volume"): "1, Cap, Vol Title"}
    assert mets.editors == [('personal', {'family': 'EditorFam', 'given': 'EditorGiv'})]
    assert mets.authors == [('corporate', {None: 'CorpAuthor'})]
    assert mets.notes == ["Note 1"]
    assert mets.get_languages() == {'invalidlangcode': 'Unbekannt'}
    assert mets.get_owner_digital() == "SLUB Dresden"
    assert mets.get_license() == "Public Domain"
    assert mets.get_license_url() == ""
    assert mets.get_location_phys() == "Library"
    assert mets.get_location_urls() == ["http://example.org"]
    assert mets.get_encoding_description() == "Kitodo.Production"
    assert mets.has_digital_origin() is True
    assert mets.get_order("PHYS_0001") == 1
    assert mets.get_orderlabel("PHYS_0001") == "Page 1"
    assert mets.get_page_structure() is not None

def test_mets_more_div_types():
    from io import BytesIO

    div_types = [
        ("contained_work", "a", "DM"),
        ("article", "a", "JA"),
        ("periodical", "j", "J"),
        ("lecture", "s", ""),
        ("monograph", "m", "M"),
        ("multivolume_work", "m", "MM"),
    ]

    for div_type, exp_level, exp_type in div_types:
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods/>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:structMap TYPE="LOGICAL">
    <mets:div TYPE="{div_type}" LABEL="Div Label"/>
  </mets:structMap>
  <mets:structMap TYPE="PHYSICAL">
    <mets:div TYPE="PHYSICAL"/>
  </mets:structMap>
</mets:mets>'''.encode('utf-8')

        mets = Mets()
        mets.fromfile(BytesIO(xml_content))
        assert mets.biblevel == exp_level
        assert mets.bibtype == exp_type

def test_mets_uncovered_branches():
    from io import BytesIO

    # Test titleInfo sorted with type != 'simple'/'uniform' (e.g. type='other') to hit return 1 in norm_title_first,
    # origin_info with dateIssued without point (point is None -> "unspecified"),
    # dv:rightsMD license node present, location without shelfLocator/physicalLocation/url,
    # multiple structMaps in get_page_structure/get_div_structure.
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3" xmlns:dv="http://dfg-viewer.de/" xmlns:xlink="http://www.w3.org/1999/xlink">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo type="other">
            <mods:title>Other Title</mods:title>
          </mods:titleInfo>
          <mods:titleInfo type="abbreviated">
            <mods:title>Abbrev Title</mods:title>
          </mods:titleInfo>
          <mods:name type="personal">
            <mods:namePart>NoRoleName</mods:namePart>
          </mods:name>
          <mods:name type="personal">
            <mods:namePart>OtherRoleName</mods:namePart>
            <mods:role>
              <mods:roleTerm>other_role</mods:roleTerm>
            </mods:role>
          </mods:name>
          <mods:originInfo>
            <mods:dateIssued>1900</mods:dateIssued>
            <mods:edition>1. Ed</mods:edition>
          </mods:originInfo>
          <mods:physicalDescription>
            <mods:digitalOrigin>reformatted digital</mods:digitalOrigin>
          </mods:physicalDescription>
          <mods:part>
            <mods:detail type="chapter"/>
          </mods:part>
          <mods:location/>
          <mods:relatedItem type="series">
            <mods:titleInfo/>
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
            <dv:owner>SLUB Dresden</dv:owner>
            <dv:license>Public License</dv:license>
          </dv:rights>
        </mets:xmlData>
      </mets:mdWrap>
    </mets:rightsMD>
  </mets:amdSec>
  <mets:structMap TYPE="OTHER">
    <mets:div TYPE="OTHER"/>
  </mets:structMap>
  <mets:structMap TYPE="LOGICAL">
    <mets:div TYPE="unknown_div_type"/>
  </mets:structMap>
  <mets:structMap TYPE="PHYSICAL">
    <mets:div TYPE="PHYSICAL">
      <mets:div TYPE="page" ID="PHYS_0001"/>
    </mets:div>
  </mets:structMap>
  <mets:structLink>
    <smLink xlink:from="LOG_0001" xlink:to="PHYS_0001"/>
  </mets:structLink>
</mets:mets>'''

    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    assert mets.get_main_title() in ["Other Title", "Abbrev Title"]
    assert mets.get_dates() == {"unspecified": "1900"}
    assert mets.get_edition() == "1. Ed"
    assert mets.biblevel is None
    assert mets.bibtype is None
    assert mets.get_license() == "Public License"
    assert mets.get_encoding_date() is None
    assert mets.get_encoding_description() is None
    assert mets.get_location_phys() is None
    assert mets.get_shelf_locators() == []
    assert mets.get_scripts() == ["Unknown"]
    assert mets.get_collections() == []

    # 2. Property setters and remaining getters
    mets.fulltext_group_name = "ALT_FULLTEXT"
    assert mets.fulltext_group_name == "ALT_FULLTEXT"
    assert mets.get_location_urls() is None
    assert mets.get_publishers() == []

    # 3. Digital origin None
    mets.digital_origin = None
    assert mets.has_digital_origin() is False

def test_mets_get_struct_links_empty_and_getters():
    mets = Mets()
    assert mets.get_struct_links("NON_EXISTENT") == []
    assert mets.get_img("NON_EXISTENT") == ""
    assert mets.get_alto("NON_EXISTENT") == ""
    assert mets.get_order("NON_EXISTENT") == "0"
    assert mets.get_orderlabel("NON_EXISTENT") == ""

def test_mets_no_structmap():
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods/>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    assert mets.get_page_structure() is None
    assert mets.get_div_structure() is None

def test_mets_title_info_no_type_and_physical_desc_no_origin():
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
            <mods:title>Title Untyped</mods:title>
          </mods:titleInfo>
          <mods:titleInfo type="uniform">
            <mods:title>Uniform Title</mods:title>
          </mods:titleInfo>
          <mods:physicalDescription>
          </mods:physicalDescription>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:amdSec>
    <mets:rightsMD ID="RIGHTS1">
      <mets:mdWrap MDTYPE="OTHER">
        <mets:xmlData>
          <dv:rights xmlns:dv="http://dfg-viewer.de/"/>
        </mets:xmlData>
      </mets:mdWrap>
    </mets:rightsMD>
  </mets:amdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    assert mets.get_main_title() == "Title Untyped"
    assert mets.get_digital_origin() == ""

def test_mets_part_order_none_and_no_notes():
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
            <mods:title>Title First</mods:title>
          </mods:titleInfo>
          <mods:titleInfo type="uniform">
            <mods:title>Uniform Second</mods:title>
          </mods:titleInfo>
          <mods:physicalDescription>
            <mods:digitalOrigin>reformatted digital</mods:digitalOrigin>
          </mods:physicalDescription>
          <mods:part>
            <mods:detail type="volume">
              <mods:title>Part Title</mods:title>
            </mods:detail>
          </mods:part>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    assert mets.get_main_title() == "Title First"
    assert mets.get_digital_origin() == "reformatted digital"
    assert mets.get_volume_titles() == {("0", "volume"): "Part Title"}
    assert mets.notes == []

def test_mets_rightsmd_no_owner_no_license():
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3" xmlns:dv="http://dfg-viewer.de/">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods/>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
  <mets:amdSec>
    <mets:rightsMD ID="RIGHTS1">
      <mets:mdWrap MDTYPE="OTHER">
        <mets:xmlData>
          <dv:rights>
          </dv:rights>
        </mets:xmlData>
      </mets:mdWrap>
    </mets:rightsMD>
  </mets:amdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    assert mets.get_owner_digital() == ""
    assert mets.get_license() == ""

def test_mets_slub_license_and_origin_info_date_start():
    from io import BytesIO
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">
  <mets:dmdSec ID="DMD1">
    <mets:mdWrap MDTYPE="MODS">
      <mets:xmlData>
        <mods:mods>
          <mods:titleInfo>
          </mods:titleInfo>
          <mods:originInfo>
            <mods:dateIssued point="start">1850</mods:dateIssued>
          </mods:originInfo>
          <mods:accessCondition type="use and reproduction" href="http://example.org/license">CC-BY 4.0</mods:accessCondition>
        </mods:mods>
      </mets:xmlData>
    </mets:mdWrap>
  </mets:dmdSec>
</mets:mets>'''
    mets = Mets()
    mets.fromfile(BytesIO(xml_content))
    assert mets.get_dates() == {"start": "1850"}
    assert mets.get_license() == "CC-BY 4.0"
    assert mets.get_license_url() == "http://example.org/license"
