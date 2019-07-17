# -*- coding: utf-8 -*-

from lxml import etree

import os

import csv

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
        filep = open(os.path.realpath(resource_filename(Requirement.parse("mets_mods2teiHeader"), 'mets_mods2teiHeader/data/iso15924-utf8-20180827.txt')))
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

        self.tree = None
        self.script_iso = Iso15924()

        self.title = None
        self.sub_titles = None
        self.authors = None
        self.editors = None
        self.places = None
        self.dates = None
        self.publishers = None
        self.digital_origin = None
        self.owner_digital = None
        self.license = None
        self.license_url = None
        self.encoding_date = None
        self.encoding_desc = None
        self.owner_manuscript = None
        self.shelf_locator = None
        self.identifiers = None
        self.scripts = None
        self.collections = None

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
        self.__spur()

    def __spur(self):
        """
        Initial interpretation of the METS/MODS file.
        """
        # TODO: Check whether the first dmdSec always refers to the volume title,
        # alternatively identify the corresponding dmdSec via <structMap type="Logical" />

        #
        # main title
        self.title = self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:titleInfo/mods:title", namespaces=ns)[0].text

        #
        # sub titles
        self.sub_titles = [text.text for text in self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:titleInfo/mods:subTitle", namespaces=ns)]

        #
        # authors and editors
        self.authors = []
        self.editors = []
        for name in self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:name", namespaces=ns):
            person = {}
            typ = name.get("type", default="unspecified")
            for name_part in name.xpath("mods:namePart", namespaces=ns):
                person[name_part.get("type", default="unspecified")] = name_part.text

            # either author or editor
            roles = name.xpath("mods:role/mods:roleTerm", namespaces=ns)
            # TODO: handle the complete set of allowed roles
            for role in roles:
                if role.text == "edt":
                    self.editors.append((typ, person))
                elif role.text == "aut":
                    self.authors.append((typ, person))

        #
        # publication places
        self.places = []
        for place in self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:originInfo[1]/mods:place", namespaces=ns):
            place_ext = {}
            for place_term in place.xpath("mods:placeTerm", namespaces=ns):
                typ = place_term.get("type", default="unspecified")
                place_ext[typ] = place_term.text
            self.places.append(place_ext)

        #
        # publication dates
        self.dates = []
        for date_issued in self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:originInfo[1]/mods:dateIssued", namespaces=ns):
            date_ext = {}
            date_ext[date_issued.get("point", "unspecified")] = date_issued.text
            self.dates.append(date_ext)

        #
        # publishers
        self.publishers = []
        for publisher in self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:originInfo[1]/mods:publisher", namespaces=ns):
            self.publishers.append(publisher.text)

        #
        # digital_origin
        for digital_origin in self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:physicalDescription[1]/mods:digitalOrigin", namespaces=ns):
            self.digital_origin = digital_origin.text
            break

        #
        # owner of the digital edition
        self.owner_digital = self.tree.xpath("//mets:amdSec[1]//dv:rights/dv:owner", namespaces=ns)[0].text

        #
        # availability/license

        # common case
        license_nodes = self.tree.xpath("//mets:amdSec[1]//dv:rights/dv:license", namespaces=ns)
        if license_nodes != []:
            self.license = license_nodes[0].text
            self.license_url = ""
        # slub case
        else:
            license_nodes = self.tree.xpath("////mets:dmdSec[1]//mods:mods/mods:accessCondition[@type='use and reproduction']", namespaces=ns)
            if license_nodes != []:
                self.license = license_nodes[0].text
                self.license_url = license_nodes[0].get(XLINK + "href", "")
            else:
                self.license = ""
                self.license_url = ""

        #
        # data encoding
        header_node = self.tree.xpath("//mets:metsHdr", namespaces=ns)[0]
        self.encoding_date = header_node.get("CREATEDATE")
        for agent in header_node.xpath("//mets:agent", namespaces=ns):
            if agent.get("OTHERTYPE") == "SOFTWARE":
                self.encoding_desc = agent.xpath("//mets:name", namespaces=ns)[0].text

	#
	# location of manuscript

        # location-related elements are optional or conditional
        location = self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:location[1]", namespaces=ns)
        if location:
            shelf_locator = self.shelf_locator = location[0].xpath("//mods:shelfLocator", namespaces=ns)
            if shelf_locator:
                self.shelf_locator = shelf_locator[0].text
            physical_location = location[0].xpath("//mods:physicalLocation", namespaces=ns)
            if physical_location:
                if physical_location[0].get("displayLabel", default="unspecified") != "unspecified":
                    self.owner_manuscript = physical_location[0].get("displayLabel")
                else:
                    self.owner_manuscript = physical_location[0].text

        #
        # identifiers
        identifiers = self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:identifier", namespaces=ns)
        self.identifiers = []
        for identifier in identifiers:
            self.identifiers.append((identifier.get("type", default="unknown"), identifier.text))

        #
        # scripts
        scripts = self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:language/mods:scriptTerm", namespaces=ns)
        self.scripts = []
        for script in scripts:
            self.scripts.append(self.script_iso.get(script.text))
        if not self.scripts:
            self.scripts.append(self.script_iso.get('Unknown'))


        #
        # collections (from relatedItem)
        collections = self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:relatedItem[@type='series']", namespaces=ns)
        self.collections = []
        for collection in collections:
            title = collection.xpath("//mods:titleinfo/mods:title", namespaces=ns)
            if title:
                self.collections.append(title[0].text)


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

    def get_shelf_locator(self):
        """
        Return the shelf locator of the original manuscript
        """
        return self.shelf_locator

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
