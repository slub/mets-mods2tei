# -*- coding: utf-8 -*-

from lxml import etree
from pathlib import Path
import os
import logging
import csv
from typing import Optional, Dict, List, Union, Any, IO
import babel
from .mets_generateds import parseString as parse_mets
from .mods_generateds import parseString as parse_mods
from .util import resource_filename

NS = {
    'mets': "http://www.loc.gov/METS/",
    'mods': "http://www.loc.gov/mods/v3",
    'xlink': "http://www.w3.org/1999/xlink",
    'dv': "http://dfg-viewer.de/",
}
METS = "{%s}" % NS['mets']
XLINK = "{%s}" % NS['xlink']


class Iso15924:
    """A class to handle ISO 15924 script codes."""

    def __init__(self) -> None:
        """
        Initialize the Iso15924 instance.

        Loads the ISO 15924 script codes and their English names into a map.
        """
        self.map: Dict[str, str] = {}
        with open(resource_filename('mets_mods2tei', 'data/iso15924-utf8-20180827.txt')) as filep:
            reader = csv.DictReader(
                filter(lambda row: row[0] != '#', filep),
                delimiter=';',
                quoting=csv.QUOTE_NONE,
                fieldnames=['code', 'index', 'name_eng', 'name_fr', 'alias', 'Age', 'Date']
            )
            for row in reader:
                self.map[row['code']] = row['name_eng']

    def get(self, code: str) -> str:
        """
        Return the description for the given ISO 15924 code.

        Args:
            code (str): An ISO 15924 code.

        Returns:
            str: The English name of the script, or "Unknown" if the code is not found.
        """
        return self.map.get(code, "Unknown")


class Mets:
    """A class to handle METS (Metadata Encoding and Transmission Standard) files."""

    def __init__(self) -> None:
        """
        Initialize the Mets instance.

        Sets up the internal data structures and default values for handling METS files.
        """
        self.script_iso: Iso15924 = Iso15924()
        self.tree: Optional[etree._ElementTree] = None
        self.wd: str = os.getcwd()
        self.mets: Optional[Any] = None
        self.mods: Optional[Any] = None
        self.page_map: Dict[str, Any] = {}
        self.order_map: Dict[str, str] = {}
        self.orderlabel_map: Dict[str, str] = {}
        self.img_map: Dict[str, str] = {}
        self.alto_map: Dict[str, str] = {}
        self.struct_links: Dict[str, List[str]] = {}
        self.fulltext_group_name: str = 'FULLTEXT'
        self.image_group_name: str = 'DEFAULT'

        self.title: Optional[str] = None
        self.sub_titles: Optional[List[str]] = None
        self.part_titles: Optional[Dict[str, str]] = None
        self.volume_titles: Optional[Dict[str, str]] = None
        self.authors: Optional[List[Dict[str, str]]] = None
        self.editors: Optional[List[Dict[str, str]]] = None
        self.places: Optional[List[Dict[str, str]]] = None
        self.dates: Optional[Dict[str, str]] = None
        self.notes: Optional[List[str]] = None
        self.publishers: Optional[List[str]] = None
        self.edition: Optional[str] = None
        self.digital_origin: Optional[str] = None
        self.owner_digital: Optional[str] = None
        self.license: Optional[str] = None
        self.license_url: Optional[str] = None
        self.encoding_date: Optional[str] = None
        self.encoding_desc: Optional[str] = None
        self.location_phys: Optional[str] = None
        self.location_urls: Optional[List[str]] = None
        self.shelf_locators: Optional[List[str]] = None
        self.identifiers: Optional[Dict[str, str]] = None
        self.scripts: Optional[List[str]] = None
        self.collections: Optional[List[str]] = None
        self.languages: Optional[Dict[str, str]] = None
        self.classifications: Optional[Dict[str, List[str]]] = None
        self.subjects: Optional[Dict[str, List[str]]] = None
        self.extents: Optional[List[str]] = None
        self.series: Optional[List[str]] = None

        # Logging
        self.logger: logging.Logger = logging.getLogger(__name__)

    @classmethod
    def read(cls, source: Union[str, IO]) -> 'Mets':
        """
        Read a METS file from a given source.

        Args:
            source: The METS file source, which can be a file path or a file-like object.

        Returns:
            Mets: An instance of the Mets class.
        """
        if hasattr(source, 'read'):
            return cls.from_file(source)
        if Path(source).exists():
            return cls.from_file(source)

    @classmethod
    def from_file(cls, path: Union[str, IO]) -> 'Mets':
        """
        Read a METS file from a given file path.

        Args:
            path (str): The path to the METS file.

        Returns:
            Mets: An instance of the Mets class.
        """
        instance = cls()
        instance.fromfile(path)
        return instance

    def fromfile(self, path: Union[str, IO]) -> None:
        """
        Parse a METS file from a given file path.

        Args:
            path (str): The path to the METS file.
        """
        if hasattr(path, 'read'):
            if hasattr(path, 'name'):
                # open file
                self.wd = os.path.dirname(path.name)
            else:
                # download stream
                pass # keep cwd
        else:
            self.wd = os.path.dirname(path)
        self.tree = etree.parse(path)
        self.mets = parse_mets(
            etree.tostring(self.tree.getroot().xpath('//mets:mets', namespaces=NS)[0]),
            silence=True
        )
        self.mods = parse_mods(
            self.mets.get_dmdSec()[0].get_mdWrap().get_xmlData().get_anytypeobjs_()[0],
            silence=True
        )
        self.__spur()

    def __spur(self) -> None:
        """
        Perform the initial interpretation of the METS/MODS file.

        This method extracts and organizes metadata from the METS/MODS file.
        """
        #
        # get publication level
        # get main and sub title from top-level logical div as a fallback
        self.title = ""
        self.biblevel = None
        self.bibtype = None
        div = self.get_div_structure()
        if div:
            self.title = div.get_LABEL() # overridden by any titleInfo
            div_type = div.get_TYPE()
            # differentiate between analytic and closed, periodic and singular, dependent and indepenent types
            # (for use in bibl/@type and biblFull//title/@level):
            # FIXME: verify this ruleset is correct/standardized (but criteria do not look orthogonal, e.g. "issue" and "proceeding")
            if div_type in ["bachelor_thesis", "diploma_thesis", "magister_thesis", "master_thesis", "doctoral_thesis", "habilitation_thesis", "file", "register", "research_paper", "report", "atlas", "album", "letter", "document", "leaflet", "manuscript", "poster", "plan", "study", "judgement", "preprint", "dossier", "paper"]:
                self.biblevel = 'u' # unpublished
                self.bibtype = 'M' # monograph
            elif div_type in ["contained_work", "folder", ]:
                self.biblevel = 'a'
                self.bibtype = 'DM' # dependent part of monograph
                # ? or 'DS' # dependent part of series
            elif div_type in ["article"]:
                self.biblevel = 'a' # analytic
                self.bibtype = 'JA' # journal article
            elif div_type in ["periodical", "newspaper"]:
                self.biblevel = 'j' # journal
                self.bibtype = 'J' # journal
            elif div_type in ["lecture"]:
                self.biblevel = 's' # series
                self.bibtype = '' # ?
            elif div_type in ["monograph", ]:
                self.biblevel = 'm' # monograph
                self.bibtype = 'M' # monograph
            elif div_type in ["multivolume_work", "volume"]:
                self.biblevel = 'm' # monograph
                self.bibtype = 'MM' # monograph within multi-volume monograph
                # ? or 'MS' # monograph within series
                # ? or 'MMS' # monograph within multi-volume monograph series

        #
        # titleInfo (main, sub, part/volume)
        self.sub_titles = [] # subtitle (mods:titleInfo[mods:subTitle]
        self.part_titles = dict() # part title of multipart subseries (mods:titleInfo[mods:partNumber|mods:partName])
        self.volume_titles = dict() # volume title in multivolume monograph (mods:part[mods:detail])
        title_infos = self.mods.get_titleInfo()
        if len(title_infos):
            def norm_title_first(titleInfo):
                if not titleInfo.get_type() or titleInfo.get_type() == 'simple':
                    # prefer untyped entry ('simple' most likely is from generateDS)
                    return -1
                if titleInfo.get_type() == 'uniform':
                    return 0
                return 1
            title_info = sorted(title_infos, key=norm_title_first)[0]
            if title_info.get_title():
                self.title = title_info.get_title()[0].get_valueOf_().strip()
            for sub_title in title_info.get_subTitle():
                self.sub_titles.append(sub_title.get_valueOf_().strip())
            for part_number, part_name in zip(title_info.get_partNumber(), title_info.get_partName()):
                self.part_titles[part_number.get_valueOf_().strip()] = part_name.get_valueOf_().strip()
        part_infos = self.mods.get_part()
        if len(part_infos):
            part_info = part_infos[0]
            order = str(part_info.get_order() or 0)
            for detail in part_info.get_detail():
                typ = detail.get_type()
                val = ', '.join([title.get_valueOf_().strip()
                                 for title in detail.get_number() + detail.get_caption() + detail.get_title()])
                self.volume_titles[order, typ] = val

        #
        # authors and editors
        self.authors = []
        self.editors = []
        for name in self.mods.get_name():
            person = {}
            typ = name.get_type()
            for name_part in name.get_namePart():
                person[name_part.get_type()] = name_part.get_valueOf_()

            # either author or editor
            roles = name.get_role()[0].get_roleTerm() if name.get_role() else []
            # TODO: handle the complete set of allowed roles
            for role in roles:
                if role.get_valueOf_() == "edt":
                    self.editors.append((typ, person))
                elif role.get_valueOf_() == "aut":
                    self.authors.append((typ, person))

        notes = self.mods.get_note()
        if notes:
            self.notes = [note.get_valueOf_() for note in notes]
        else:
            self.notes = []

        #
        # orgin info
        origin_info = self.mods.get_originInfo()

        # publication place
        self.places = []
        if origin_info:
            for place in origin_info[0].get_place():
                place_ext = {}
                for place_term in place.get_placeTerm():
                    place_ext[place_term.get_type() or 'text'] = place_term.get_valueOf_()
                self.places.append(place_ext)

        # publication dates
        self.dates = {}
        if origin_info:
            for date_issued in origin_info[0].get_dateIssued():
                date_type = date_issued.get_point() if date_issued.get_point() != None else "unspecified"
                self.dates[date_type] = date_issued.get_valueOf_()

        # publishers
        self.publishers = []
        if origin_info:
            for publisher in origin_info[0].get_publisher():
                self.publishers.append(publisher.get_valueOf_())

        # edition of the manuscript
        self.edition = ""
        if origin_info and origin_info[0].get_edition():
            self.edition = origin_info[0].get_edition()[0].get_valueOf_()

        #
        # languages and scripts
        languages = self.mods.get_language()

        self.languages = {}
        self.scripts = []
        for language in languages:
            for language_term in language.get_languageTerm():
                try:
                    self.languages[language_term.get_valueOf_()] = babel.Locale.parse(language_term.get_valueOf_()).get_language_name('de')
                except babel.core.UnknownLocaleError as err:
                    self.logger.error("{0}. Falling back to 'Unbekannt'".format(err))
                    self.languages[language_term.get_valueOf_()] = "Unbekannt"
            for script_term in language.get_scriptTerm():
                self.scripts.append(self.script_iso.get(script_term.get_valueOf_()))
        if not self.languages:
            self.languages['mis'] = 'Unkodiert'
        if not self.scripts:
            self.scripts.append(self.script_iso.get('Unknown'))

        #
        # classifications and subjects
        classifications = self.mods.get_classification()
        self.classifications = dict()
        if classifications:
            for classification in classifications:
                codes = self.classifications.setdefault(classification.get_authority(), list())
                codes.append(classification.get_valueOf_())
        subjects = self.mods.get_subject()
        self.subjects = dict()
        if subjects:
            for subject in subjects:
                keywords = self.subjects.setdefault(subject.get_authority(), list())
                for topic in subject.topic:
                    keywords.append(('topic', topic.get_valueOf_()))
                for geographic in subject.geographic:
                    keywords.append(('geographic', geographic.get_valueOf_()))
                for temporal in subject.temporal:
                    keywords.append(('temporal', temporal.get_valueOf_()))

        #
        # physical description
        physical_description = self.mods.get_physicalDescription()

        # digital origin
        self.digital_origin = ""
        if physical_description and physical_description[0].get_digitalOrigin():
            self.digital_origin = physical_description[0].get_digitalOrigin()[0]

        # extent
        self.extents = []
        if physical_description:
            for extent in physical_description[0].get_extent():
                self.extents.append(extent.get_valueOf_())

        #
        # dv FIXME: replace with generated code as soon as schema is available
        amdsec = self.mets.get_amdSec()
        if amdsec and amdsec[0].get_rightsMD():
            dv = etree.fromstring(amdsec[0].get_rightsMD()[0].get_mdWrap().get_xmlData().get_anytypeobjs_()[0])
        else:
            dv = None

        # owner of the digital edition
        owner = dv.xpath("//dv:owner", namespaces=NS) if dv is not None else []
        self.owner_digital = owner[0].text if len(owner) else ""

        # availability/license
        # common case
        self.license = ""
        self.license_url = ""
        license_nodes = dv.xpath("//dv:license", namespaces=NS) if dv is not None else []
        if len(license_nodes):
            self.license = license_nodes[0].text
            self.license_url = ""
        # slub case
        else:
            license_nodes = self.mods.get_accessCondition()
            for license_node in license_nodes:
                if license_node.get_type() == 'use and reproduction':
                    self.license = license_node.get_valueOf_()
                    self.license_url = license_node.get_href() if license_node.get_href() else ""

        #
        # metsHdr
        header = self.mets.get_metsHdr()
        if header:
            # encoding date
            self.encoding_date = header.get_CREATEDATE()
            # encoding description
            self.encoding_desc = [agent.get_name()
                                  for agent in header.get_agent()
                                  if agent.get_TYPE() == "OTHER" and agent.get_OTHERTYPE() == "SOFTWARE"]
        else:
            self.encoding_date = None
            self.encoding_desc = None

        if self.encoding_date:
            self.encoding_date = self.encoding_date.isoformat()
        else:
            self.logger.error("Found no @CREATEDATE for publicationStmt/date")
        if self.encoding_desc:
            self.encoding_desc = self.encoding_desc[0] # or -1?
            # what about agent.get_OTHERROLE() and agent.get_note()?
        else:
            self.logger.warning("Found no mets:agent for encodingDesc")

	#
	# location of manuscript

        # location-related elements are optional or conditional
        self.shelf_locators = []
        if self.mods.get_location():
            location = self.mods.get_location()[0]
            if location.get_shelfLocator():
                self.shelf_locators.extend([shelf_locator.get_valueOf_() for shelf_locator in location.get_shelfLocator()])
            if location.get_physicalLocation():
                self.location_phys = location.get_physicalLocation()[0].get_valueOf_()
            if location.get_url():
                self.location_urls = [url.get_valueOf_() for url in location.get_url()]

        #
        # URN and VD ID
        self.identifiers = dict()
        identifiers = self.mods.get_identifier()
        if len(identifiers):
            for identifier in identifiers:
                self.identifiers[identifier.get_type()] = identifier.get_valueOf_()

        #
        # collections (from relatedItem)
        self.collections = []
        collections = filter(lambda x: x.get_type() == "series", self.mods.get_relatedItem())
        for collection in collections:
            title = collection.get_titleInfo()[0].get_title()
            if title:
                self.collections.append(title[0].get_valueOf_())

        #
        # file groups

        # fulltext
        fulltext_map = {}
        fulltext_group = self.tree.xpath("//mets:fileGrp[@USE='%s']" % self.fulltext_group_name, namespaces=NS)
        if fulltext_group:
            fulltext_map = {}
            for entry in fulltext_group[0].xpath("./mets:file", namespaces=NS):
                url = entry.find("./" + METS + "FLocat").get("%shref" % XLINK)
                self.logger.debug("Found full-text file: %s", url)
                fulltext_map[entry.get("ID")] = url

        # image
        image_map = {}
        image_group = self.tree.xpath("//mets:fileGrp[@USE='%s']" % self.image_group_name, namespaces=NS)
        if image_group:
            for entry in image_group[0].xpath("./mets:file", namespaces=NS):
                url = entry.find("./" + METS + "FLocat").get("%shref" % XLINK)
                self.logger.debug("Found image file: %s", url)
                image_map[entry.get("ID")] = url

        # struct map physical
        for div in self.get_page_structure().get_div():
            page = div.get_ID()
            self.logger.debug("Found physical page: %s", page)
            self.page_map[page] = div
            if div.get_ORDER():
                self.order_map[page] = div.get_ORDER()
            if div.get_ORDERLABEL():
                self.orderlabel_map[page] = div.get_ORDERLABEL()
            for fptr in div.get_fptr():
                if fptr.get_FILEID() in fulltext_map:
                    self.alto_map[page] = fulltext_map[fptr.get_FILEID()]
                elif fptr.get_FILEID() in image_map:
                    self.img_map[page] = image_map[fptr.get_FILEID()]

        # struct links
        structlinks = self.tree.xpath("//mets:structLink/*", namespaces=NS)
        for sm_link in structlinks:
            logical = sm_link.get("%sfrom" % XLINK)
            physical = sm_link.get("%sto" % XLINK)
            if physical in self.alto_map:
                self.logger.debug("Found structLink from %s to physical page: %s", logical, physical)
                pages = self.struct_links.setdefault(logical, list())
                pages.append(physical)

    @property
    def fulltext_group_name(self) -> str:
        """
        Get the full-text-related file group use attribute.

        Returns:
            str: The full-text group name.
        """
        return self.__fulltext_group_name

    @fulltext_group_name.setter
    def fulltext_group_name(self, fulltext_use: str) -> None:
        """
        Set the full-text-related file group use attribute.

        Args:
            fulltext_use (str): The new full-text group name.
        """
        self.__fulltext_group_name = fulltext_use

    def get_main_title(self):
        """
        Return the main title of the work.
        """
        return self.title

    def get_sub_titles(self):
        """
        Return the sub-titles of the work.
        """
        return self.sub_titles

    def get_part_titles(self):
        """
        Return the part titles of the work.
        """
        return self.part_titles

    def get_volume_titles(self):
        """
        Return the volume titles of the work.
        """
        return self.volume_titles

    def get_authors(self):
        """
        Return the author of the work.
        """
        return self.authors

    def get_places(self):
        """
        Return the place(s) of publication.
        """
        return self.places

    def get_dates(self):
        """
        Return the date(s) of publication.
        """
        return self.dates

    def get_publishers(self):
        """
        Return the publishers.
        """
        return self.publishers

    def get_edition(self):
        """
        Return the edition of the source manuscript.
        """
        return self.edition

    def has_digital_origin(self):
        """
        Element "digitalOrigin" present?
        """
        return self.digital_origin != None

    def get_digital_origin(self):
        """
        Return the digital origin.
        """
        return self.digital_origin

    def get_owner_digital(self):
        """
        Return the owner of the digital edition.
        """
        return self.owner_digital

    def get_license(self):
        """
        Return the license of the digital edition.
        """
        return self.license

    def get_license_url(self):
        """
        Return the url of the license of the digital edition.
        """
        return self.license_url

    def get_encoding_date(self):
        """
        Return the date of encoding for the digital edition.
        """
        return self.encoding_date

    def get_encoding_description(self):
        """
        Return details on the encoding of the digital edition.
        """
        return self.encoding_desc

    def get_location_phys(self):
        """
        Return the physical location of the original manuscript.
        """
        return self.location_phys

    def get_location_urls(self):
        """
        Return the URL location of the original manuscript.
        """
        return self.location_urls

    def get_shelf_locators(self):
        """
        Return the shelf locators of the original manuscript.
        """
        return self.shelf_locators

    def get_identifiers(self):
        """
        Return the (dict of) identifiers of the digital representation.
        """
        return self.identifiers

    def get_scripts(self):
        """
        Return information on the dominant fonts.
        """
        return self.scripts

    def get_collections(self):
        """
        Return the name of the collections of the digital edition.
        """
        return self.collections

    def get_languages(self):
        """
        Return the languages used in the original manuscript.
        """
        return self.languages

    def get_page_structure(self):
        """
        Return the div structure from the physical struct map.
        """
        for struct_map in self.mets.get_structMap():
            if struct_map.get_TYPE() == "PHYSICAL":
                return struct_map.get_div()
        return None

    def get_div_structure(self):
        """
        Return the div structure from the logical struct map.
        """
        for struct_map in self.mets.get_structMap():
            if struct_map.get_TYPE() == "LOGICAL":
                return struct_map.get_div()
        return None

    def get_struct_links(self, log_id):
        """
        Return the list of physical pages for a logical ID.
        """
        return self.struct_links.get(log_id, [])

    def get_img(self, phys_id):
        """
        Return an image link for a given physical ID.
        """
        return self.img_map.get(phys_id, "")

    def get_alto(self, phys_id):
        """
        Return the ALTO link for a given physical ID.
        """
        return self.alto_map.get(phys_id, "")

    def get_order(self, phys_id):
        """
        Return the logical (manually set) page number for a given physical ID.
        """
        return self.order_map.get(phys_id, "0")

    def get_orderlabel(self, phys_id):
        """
        Return the logical (manually set) page label for a given physical ID.
        """
        return self.orderlabel_map.get(phys_id, "")
