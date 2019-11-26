# -*- coding: utf-8 -*-

from lxml import etree
import os
import csv
import babel

from .mets_generateds import parseString as parse_mets
from .mods_generateds import parseString as parse_mods

from pkg_resources import resource_filename, Requirement

ns = {
     'mets': "http://www.loc.gov/METS/",
     'mods': "http://www.loc.gov/mods/v3",
     'xlink': "http://www.w3.org/1999/xlink",
     'dv': "http://dfg-viewer.de/",
}
METS = "{%s}" % ns['mets']
XLINK = "{%s}" % ns['xlink']

class Iso15924:

    def __init__(self):
        """
        The constructor.
        """
        self.map = {}
        filep = open(os.path.realpath(resource_filename(Requirement.parse("mets_mods2tei"), 'mets_mods2tei/data/iso15924-utf8-20180827.txt')))
        reader = csv.DictReader(filter(lambda row: row[0]!='#', filep), delimiter=';', quoting=csv.QUOTE_NONE, fieldnames=['code','index','name_eng', 'name_fr', 'alias', 'Age', 'Date'])
        for row in reader:
            self.map[row['code']] = row['name_eng']
        filep.close()

    def get(self, code):
        """
        Return the description for the given code
        :param str: An ISO 15924 code
        """
        return self.map.get(code, "Unknown")

class Mets:

    def __init__(self):
        """
        The constructor.
        """

        self.script_iso = Iso15924()

        self.tree = None
        self.mets = None
        self.mods = None
        self.alto_map = {}
        self.alto_list = {}

        self.title = None
        self.sub_titles = None
        self.authors = None
        self.editors = None
        self.places = None
        self.dates = None
        self.publishers = None
        self.edition = None
        self.digital_origin = None
        self.owner_digital = None
        self.license = None
        self.license_url = None
        self.encoding_date = None
        self.encoding_desc = None
        self.owner_manuscript = None
        self.shelf_locators = None
        self.identifiers = None
        self.scripts = None
        self.collections = None
        self.languages = None
        self.extents = None
        self.series = None

    @classmethod
    def read(cls, source):
        """
        Reads in METS from a given (file) source.
        :param source: METS (file) source.
        """
        if hasattr(source, 'read'):
            return cls.fromfile(source)
        if os.path.exists(source):
            return cls.fromfile(source)

    @classmethod
    def fromfile(cls, path):
        """
        Reads in METS from a given file source.
        :param str path: Path to a METS document.
        """
        i = cls()
        i.__fromfile(path)
        return i

    def __fromfile(self, path):
        """
        Reads in METS from a given file source.
        :param str path: Path to a METS document.
        """
        self.tree = etree.parse(path)
        self.mets = parse_mets(etree.tostring(self.tree.getroot().xpath('//mets:mets', namespaces=ns)[0]), silence=True)
        self.mods = parse_mods(self.mets.get_dmdSec()[0].get_mdWrap().get_xmlData().get_anytypeobjs_()[0], silence=True)
        self.__spur()

    def __spur(self):
        """
        Initial interpretation of the METS/MODS file.
        """

        #
        # main title and manuscript type
        struct_map_logical = list(filter(lambda x: x.get_TYPE() == "LOGICAL", self.mets.get_structMap()))[0]
        title = struct_map_logical.get_div()
        self.title = title.get_LABEL()
        self.type = title.get_TYPE()

        #
        # sub titles
        self.sub_titles = [sub_title.get_valueOf_().strip() for sub_title in self.mods.get_titleInfo()[0].get_subTitle()]

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
            roles = name.get_role()[0].get_roleTerm()
            # TODO: handle the complete set of allowed roles
            for role in roles:
                if role.get_valueOf_() == "edt":
                    self.editors.append((typ, person))
                elif role.get_valueOf_() == "aut":
                    self.authors.append((typ, person))

        #
        # orgin info
        origin_info = self.mods.get_originInfo()[0]

        # publication place
        self.places = []
        for place in origin_info.get_place():
            place_ext = {}
            for place_term in place.get_placeTerm():
                place_ext[place_term.get_type()] = place_term.get_valueOf_()
            self.places.append(place_ext)

        # publication dates
        self.dates = {}
        for date_issued in origin_info.get_dateIssued():
            date_type = date_issued.get_point() if date_issued.get_point() != None else "unspecified"
            self.dates[date_type] = date_issued.get_valueOf_()

        # publishers
        self.publishers = []
        for publisher in origin_info.get_publisher():
            self.publishers.append(publisher.get_valueOf_())

        # edition of the manuscript
        self.edition = origin_info.get_edition()[0].get_valueOf_() if origin_info.get_edition() else ""

        #
        # languages and scripts
        languages = self.mods.get_language()
        
        self.languages = {}
        self.scripts = []
        for language in languages:
            for language_term in language.get_languageTerm():
                self.languages[language_term.get_valueOf_()] = babel.Locale.parse(language_term.get_valueOf_()).get_language_name('de')
            for script_term in language.get_scriptTerm():
                self.scripts.append(self.script_iso.get(script_term.get_valueOf_()))
        if not self.languages:
            self.languages['mis'] = 'Unkodiert'
        if not self.scripts:
            self.scripts.append(self.script_iso.get('Unknown'))

        #
        # physical description
        physical_description = self.mods.get_physicalDescription()[0]

        # digital origin
        self.digital_origin = physical_description.get_digitalOrigin()[0] if physical_description.get_digitalOrigin() else ""

        # extent
        self.extents = []
        for extent in physical_description.get_extent():
            self.extents.append(extent.get_valueOf_())

        #
        # dv FIXME: replace with generated code as soon as schema is available
        dv = etree.fromstring(self.mets.get_amdSec()[0].get_rightsMD()[0].get_mdWrap().get_xmlData().get_anytypeobjs_()[0])

        # owner of the digital edition
        self.owner_digital = dv.xpath("//dv:owner", namespaces=ns)[0].text

        # availability/license
        # common case
        self.license = ""
        self.license_url = ""
        license_nodes = dv.xpath("//dv:license", namespaces=ns)
        if license_nodes != []:
            self.license = license_nodes[0].text
            self.license_url = ""
        # slub case
        else:
            license_nodes = self.mods.get_accessCondition()
            for license_node in license_nodes:
                if license_node.get_type() == 'use and reproduction':
                    self.license = license_node.get_valueOf_()
                    self.license_url = license_node.get_href()

        #
        # metsHdr
        header = self.mets.get_metsHdr()

        # encoding date
        self.encoding_date = header.get_CREATEDATE().isoformat()

        # encoding description
        self.encoding_desc = list(filter(lambda x: x.get_OTHERTYPE() == "SOFTWARE", header.get_agent()))[0].get_name()

	#
	# location of manuscript

        # location-related elements are optional or conditional
        self.shelf_locators = []
        for location in self.mods.get_location():
            if location.get_shelfLocator():
                self.shelf_locators.extend([shelf_locator.get_valueOf_() for shelf_locator in location.get_shelfLocator()])
            elif location.get_physicalLocation():
                self.owner_manuscript = location.get_physicalLocation()

        #
        # identifiers
        self.identifiers = []
        identifiers = self.mods.get_identifier()
        for identifier in identifiers:
            self.identifiers.append((identifier.get_type(), identifier.get_valueOf_()))


        #
        # collections (from relatedItem)
        self.collections = []
        collections = filter(lambda x: x.get_type() == "series", self.mods.get_relatedItem())
        for collection in collections:
            title = collection.get_titleInfo()[0].get_title()
            if title:
                self.collections.append(title[0].get_valueOf_())

        #
        # alto map
        #fulltext_group = list(filter(lambda x: x.get_USE() == 'FULLTEXT', self.mets.get_fileSec().get_fileGrp()))[0]
        fulltext_group = self.tree.xpath("//mets:fileGrp[@USE='FULLTEXT']", namespaces=ns)[0]
        fulltext_map = {}
        for entry in fulltext_group.xpath("./mets:file", namespaces=ns):
            fulltext_map[entry.get("ID")] = entry.find("./" + METS + "FLocat").get("%shref" % XLINK)
        phys_struct_map = {}
        for div in list(filter(lambda x: x.get_TYPE() == 'PHYSICAL', self.mets.get_structMap()))[0].get_div().get_div():
            for fptr in div.get_fptr():
                if fptr.get_FILEID() in fulltext_map:
                    phys_struct_map[div.get_ID()] = fulltext_map[fptr.get_FILEID()]
                    break
        for sm_link in self.tree.xpath("//mets:structLink", namespaces=ns)[0].iterchildren():
            if sm_link.get("%sto" % XLINK) in phys_struct_map:
                if sm_link.get("%sfrom" % XLINK) not in self.alto_map:
                    self.alto_map[sm_link.get("%sfrom" % XLINK)] = []
                self.alto_map[sm_link.get("%sfrom" % XLINK)].append(phys_struct_map[sm_link.get("%sto" % XLINK)])
        

    def get_main_title(self):
        """
        Return the main title of the work.
        """
        return self.title

    def get_sub_titles(self):
        """
        Return the main title of the work.
        """
        return self.sub_titles

    def get_authors(self):
        """
        Return the author of the work.
        """
        return self.authors

    def get_places(self):
        """
        Return the place(s) of publication
        """
        return self.places

    def get_dates(self):
        """
        Return the date(s) of publication
        """
        return self.dates

    def get_publishers(self):
        """
        Return the publishers
        """
        return self.publishers

    def get_edition(self):
        """
        Return the edition of the source manuscript
        """
        return self.edition

    def has_digital_origin(self):
        """
        Element "digitalOrigin" present?
        """
        return self.digital_origin != None

    def get_digital_origin(self):
        """
        Return the digital origin
        """
        return self.digital_origin

    def get_owner_digital(self):
        """
        Return the owner of the digital edition
        """
        return self.owner_digital

    def get_license(self):
        """
        Return the license of the digital edition
        """
        return self.license

    def get_license_url(self):
        """
        Return the url of the license of the digital edition
        """
        return self.license_url

    def get_encoding_date(self):
        """
        Return the date of encoding for the digital edition
        """
        return self.encoding_date

    def get_encoding_description(self):
        """
        Return details on the encoding of the digital edition
        """
        return self.encoding_desc

    def get_owner_manuscript(self):
        """
        Return the owner of the original manuscript
        """
        return self.owner_manuscript

    def get_shelf_locators(self):
        """
        Return the shelf locators of the original manuscript
        """
        return self.shelf_locators

    def get_identifiers(self):
        """
        Return the mods identifiers as a attribut-value mapping
        """
        return self.identifiers

    def get_scripts(self):
        """
        Returns information on the dominant fonts
        """
        return self.scripts

    def get_collections(self):
        """
        Returns the name of the collections of the digital edition
        """
        return self.collections

    def get_languages(self):
        """
        Returns the languages used in the original manuscript
        """
        return self.languages

    def get_div_structure(self):
        """
        Return the div structure from the logical struct map
        """
        for struct_map in self.mets.get_structMap():
            if struct_map.get_TYPE() == "LOGICAL":
                return struct_map.get_div()
        return []

    def get_alto(self, log_id):
        """
        Return the list of ALTO links for a given LOG_ID
        """
        return self.alto_map[log_id]
