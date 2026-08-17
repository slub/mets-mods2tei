# -*- coding: utf-8 -*-

from lxml import etree

import os
import logging
import copy
import re
import mimetypes

import requests
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urlparse

from .util import resource_filename
from .alto import Alto

NS = {
     'tei': "http://www.tei-c.org/ns/1.0",
}
TEI = "{%s}" % NS['tei']

# FIXME: add more structural mappings from METS-Anwendungsprofil (DFG Strukturdatenset) to TEI-P5 tagset (DTAbf)
DIV_METS2TEI = {
    "article": "chapter",
    # misfit...
    "contained_work": "chapter",
    "contents": "contents",
    "corrigenda": "corrigenda",
    "dedication": "dedication",
    "index": "index",
    "imprint": "imprint",
    # not in DFG Strukturdatenset, but maybe used as @(ORDER)LABEL:
    "Imprimatur": "imprimatur",
    "privileges": "copyright",
    "provenance": "",
    # not in DFG Strukturdatenset, but maybe used as @(ORDER)LABEL:
    "appendix": "appendix",
    "additional": "appendix",
    "addendum": "appendix",
    "attached_work": "appendix",
    "advertising": "advertisement",
    "preface": "preface",
    "epilogue": "postface",
    "chapter": "chapter",
    "letter": "letter",
    "verse": "poem",
    "?": "diaryEntry",
    "?": "recipe",
    "?": "scene",
    "?": "act",
    "engraved_titlepage": "frontispiece",
    "?": "bibliography",
    "list_illustrations?": "figures",
    "?": "abbreviations",
    "?": "edition",
    "cover": "",
    "cover_front": "",
    "cover_back": "",
    "table": "appendix?",
    "manuscript": "?",
    "illustration": "?",
    "section": "chapter?",
}

class Tei:

    def __init__(self):
        """
        The constructor.
        """

        with open(resource_filename('mets_mods2tei', 'data/tei_skeleton.xml')) as skeleton:
            self.tree = etree.parse(skeleton)
        self.alto_map = {}

        # logging
        self.logger = logging.getLogger(__name__)
        self.refs = []

    def tostring(self):
        """
        Serializes the TEI object as xml string.
        """
        # needs lxml>=4.5:
        etree.indent(self.tree, space="  ")
        for lb in self.tree.xpath('//tei:lb', namespaces=NS):
            prefix = lb.getparent().text
            lb.tail += "  " + prefix
        return etree.tostring(self.tree, pretty_print=True, encoding="utf-8")

    def fill_from_mets(self, mets, ocr=True, refs=None):
        """
        Fill the contents of the TEI object from a METS instance
        """

        if refs:
            self.refs = refs
        #
        # replace skeleton values by real ones

        # main title
        self.set_main_title(mets.get_main_title())
        for sub in mets.get_sub_titles():
            self.add_sub_title(sub)
        for number, part in mets.get_part_titles().items():
            self.add_part_title(number, part)
        for (order, typ), volume in mets.get_volume_titles().items():
            self.add_volume_title(order, typ, volume)
        self.init_biblFull()

        # publication level
        self.set_publication_level(mets.biblevel or 'u')

        # authors
        for typ, author in mets.get_authors():
            self.add_author(author,typ)

        # notes
        for note in mets.notes:
            self.add_note(note)

        # places
        for place in mets.get_places():
            self.add_place(place)

        # dates
        self.add_date(mets.get_dates())

        # publishers
        for publisher in mets.get_publishers():
            self.add_publisher(publisher)

        # manuscript edition
        if mets.get_edition():
            self.add_source_edition(mets.get_edition())

        # digital edition
        if mets.has_digital_origin():
            self.add_digital_edition(mets.get_digital_origin())

        # hosting institution
        self.add_hoster(mets.get_owner_digital())

        # availability
        if mets.get_license() != "":
            self.set_availability("licence", mets.get_license(), mets.get_license_url())
        else:
            self.set_availability("restricted", mets.get_license(), mets.get_license_url())

        # encoding
        self.add_encoding_date(mets.get_encoding_date())
        self.set_encoding_description(mets.get_encoding_description())

        # repository
        if mets.get_location_phys():
            # hard to distinguish between settlement, institution and repository at this point
            self.add_repository(mets.get_location_phys())
        if mets.get_location_urls():
            for url in mets.get_location_urls():
                # hard to determine type of URL at this point – could be (some form of) presentation,
                # URN, PPN, EPN, DOI, URLWeb, URLCatalogue, URLImages, URLText, URLHTML, URLXML, URLTCF, URLIIIF
                if url.startswith("urn:"):
                    typ = "URN"
                elif re.fullmatch("10[.][0-9]*/.*", url):
                    typ = "DOI"
                elif re.fullmatch("[0-9]{8}[0-9X]{1,2}", url):
                    typ = "PPN"
                elif re.fullmatch("([0-9]+-)+[0-9]+", url):
                    typ = "ISBN"
                elif re.fullmatch("[0-9]{4}-[0-9]{3}[0-9xX]", url):
                    typ = "ISSN"
                else:
                    typ = "URL"
                self.add_identifier(typ, url)

        # shelf locator
        for shelf_locator in mets.get_shelf_locators():
            self.add_identifier("shelfmark", shelf_locator)

        # identifiers
        if mets.get_identifiers():
            for type_, value in mets.get_identifiers().items():
                if type_ in ["vd16", "vd17", "vd18"]:
                    type_ = "VD"
                self.add_identifier(type_.upper(), value)

        # type description
        if mets.get_scripts():
            self.set_type_desc('\n'.join(script for script in mets.get_scripts()))

        # languages
        for ident_name in mets.get_languages().items():
            self.add_language(ident_name)

        # classes
        for scheme in mets.classifications:
            classes = mets.classifications[scheme]
            for code in classes:
                self.add_classcode(scheme, code)
        for scheme in mets.subjects:
            keywords = mets.subjects[scheme]
            self.add_keywords(scheme, keywords)

        # extents
        for extent in mets.extents:
            self.add_extent(extent)

        # collection
        for collection in mets.collections:
            self.add_collection(collection)

        #
        # citation
        self.compile_bibl(mets.bibtype)

        #
        # text part

        # div structure
        div = mets.get_div_structure()
        if div is not None:
            self.logger.debug("Found logical structMap for %s", div.get_TYPE())
            self.add_div_structure(div)
        if (not len(self.tree.xpath('//tei:text/tei:body/tei:div', namespaces=NS))
            and any(mets.alto_map)):
            self.logger.warning("Found no logical structMap divs, falling back to physical")
            pages = mets.alto_map.keys()
            if any(mets.order_map.values()):
                pages = sorted(pages, key=mets.get_order)
            self.add_physical_pages(map(mets.page_map.get, pages))
        if not len(self.tree.xpath('//tei:text/tei:body/tei:div', namespaces=NS)):
            self.logger.error("Found no logical or physical structMap div")

        # OCR
        if ocr:
            self.add_ocr_text(mets)

    @property
    def main_title(self):
        """
        Return the main title of the work represented
        by the TEI Header.
        """
        return self.tree.xpath('//tei:titleStmt/tei:title[@type="main"]', namespaces=NS)[0].text

    @property
    def subtitles(self):
        """
        Return information on the subtitle(s) of the work represented
        by the TEI Header.
        """
        return [subtitle.text for subtitle in self.tree.xpath('//tei:fileDesc/tei:titleStmt/tei:title[@type="sub"]', namespaces=NS)]

    @property
    def authors(self):
        """
        Return information on the author(s) of the work represented
        by the TEI Header.
        """
        authors = []
        for author in self.tree.xpath('//tei:fileDesc/tei:titleStmt/tei:author', namespaces=NS):
            authors.append(", ".join(author.xpath('descendant-or-self::*/text()')))
        return authors

    @property
    def publication_level(self):
        """
        Return the level of publication ('monographic' vs. 'analytic')
        """
        return self.tree.xpath('//tei:sourceDesc/tei:biblFull/tei:titleStmt/tei:title[@type="main"]', namespaces=NS)[0].get("level")

    @property
    def dates(self):
        """
        Return information on the publication date(s) of the work represented
        by the TEI Header.
        """
        return [date.text for date in self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt/tei:date', namespaces=NS)]

    @property
    def places(self):
        """
        Return information on the publication place(s) of the work represented
        by the TEI Header.
        """
        return ["%s:%s" % (place.get("corresp"), place.text) for place in self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt/tei:pubPlace', namespaces=NS)]

    @property
    def publishers(self):
        """
        Return information on the publishers of the source work represented
        by the TEI Header.
        """
        return [publisher.text for publisher in self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt/tei:publisher/tei:name', namespaces=NS)]

    @property
    def hosters(self):
        """
        Return information on the publishers of the digitalized work represented
        by the TEI Header.
        """
        return [publisher.text for publisher in self.tree.xpath('//tei:fileDesc/tei:publicationStmt/tei:publisher', namespaces=NS)]

    @property
    def availability(self):
        """
        Return information on the availability status represented
        by the TEI Header.
        """
        return self.tree.xpath('//tei:fileDesc/tei:publicationStmt/tei:availability', namespaces=NS)[0].get("status")

    @property
    def licence(self):
        """
        Return information on the licencing conditions represented
        by the TEI Header.
        """
        licence = self.tree.xpath('//tei:fileDesc/tei:publicationStmt/tei:availability/tei:licence', namespaces=NS)
        if licence:
            return licence[0].text
        else:
            return ""

    @property
    def source_editions(self):
        """
        Return information on the editions of the source work represented
        by the TEI Header.
        """
        return [source_edition.text for source_edition in self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:editionStmt/tei:edition', namespaces=NS)]

    @property
    def digital_editions(self):
        """
        Return information on the editions of the digitalized work represented
        by the TEI Header.
        """
        return [digital_edition.text for digital_edition in self.tree.xpath('//tei:fileDesc/tei:editionStmt/tei:edition', namespaces=NS)]

    @property
    def encoding_dates(self):
        """
        Return information on the publishing dates of the digitalized work represented
        by the TEI Header.
        """
        return ["%s:%s" % (encoding_date.get("type"), encoding_date.text) for encoding_date in self.tree.xpath('//tei:fileDesc/tei:publicationStmt/tei:date', namespaces=NS)]


    @property
    def encoding_description(self):
        """
        Return information on the manners of creation of the digitalized work represented
        by the TEI Header.
        """
        return "".join(self.tree.xpath('//tei:encodingDesc', namespaces=NS)[0].itertext()).strip()

    @property
    def repositories(self):
        """
        Return information on the repositories storing the work represented
        by the TEI Header.
        """
        return [repository.text for repository in self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:repository', namespaces=NS)]

    @property
    def shelfmarks(self):
        """
        Return information on the TEI-Header-represented work's (library) shelfmarks.
        """
        return [shelfmark.text for shelfmark in self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno/tei:idno[@type="shelfmark"]', namespaces=NS)]

    @property
    def purl(self):
        """
        Return information on the TEI-Header-represented work's PURL.
        """
        purl = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno/tei:idno[@type="PURL"]', namespaces=NS)
        if purl:
            return purl[0].text
        else:
            return ""

    @property
    def urn(self):
        """
        Return information on the TEI-Header-represented work's URN.
        """
        urn = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno/tei:idno[@type="URN"]', namespaces=NS)
        if urn:
            return urn[0].text
        else:
            return ""

    @property
    def vd_id(self):
        """
        Return information on the TEI-Header-represented work's VD ID.
        """
        vd_id = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno/tei:idno[@type="VD"]', namespaces=NS)
        if vd_id:
            return vd_id[0].text
        else:
            return ""

    @property
    def extents(self):
        """
        Return information on the extent of the work represented
        by the TEI Header.
        """
        return [extent.text for extent in self.tree.xpath('//tei:msDesc/tei:physDesc/tei:objectDesc/tei:supportDesc/tei:extent', namespaces=NS)]

    @property
    def collections(self):
        """
        Return information on the collections of the work represented
        by the TEI Header.
        """
        return [collection.text for collection in self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:collection', namespaces=NS)]

    @property
    def bibl(self):
        """
        Return the short citation of the work represented
        by the TEI Header.
        """
        return self.tree.xpath("//tei:fileDesc/tei:sourceDesc/tei:bibl", namespaces=NS)[0]

    def set_main_title(self, string):
        """
        Set the main title of the tei:titleStmt.
        """
        titleStmt = self.tree.xpath('//tei:titleStmt', namespaces=NS)[0]
        for node in titleStmt.xpath('tei:title[@type="main"]', namespaces=NS):
            node.text = string

    def add_sub_title(self, string):
        """
        Add a sub-title of the tei:titleStmt.
        """
        titleStmt = self.tree.xpath('//tei:titleStmt', namespaces=NS)[0]
        node = etree.Element("%stitle" % TEI)
        node.set("type", "sub")
        node.text = string
        titleStmt.append(copy.deepcopy(node))

    def add_part_title(self, number, string):
        """
        Add a part title of the tei:titleStmt.
        """
        titleStmt = self.tree.xpath('//tei:titleStmt', namespaces=NS)[0]
        node = etree.Element("%stitle" % TEI)
        node.set("type", "part")
        node.set("n", number)
        node.text = string
        titleStmt.append(copy.deepcopy(node))

    def add_volume_title(self, number, typ, string):
        """
        Add a volume title of the tei:titleStmt.
        """
        titleStmt = self.tree.xpath('//tei:titleStmt', namespaces=NS)[0]
        node = etree.Element("%stitle" % TEI)
        node.set("type", typ)
        node.set("n", number)
        node.text = string
        titleStmt.append(copy.deepcopy(node))

    def init_biblFull(self):
        """
        Set the main, sub, and part/volume titles of the tei:biblFull by copying from tei:titleStmt.
        """
        titleStmt = self.tree.xpath('//tei:titleStmt', namespaces=NS)[0]
        bibl = self.tree.xpath('//tei:sourceDesc/tei:biblFull', namespaces=NS)[0]
        bibl.append(copy.deepcopy(titleStmt))

    def set_publication_level(self, level):
        """
        Set the level of publication:
        - 'm': (monographic) the title applies to a monograph such as a book
               or other item considered to be a distinct publication,
               including single volumes of multi-volume works
        - 'a': (analytic) the title applies to an analytic item, such as an article,
               poem, or other work published as part of a larger item.
        - 'j': (journal) the title applies to any serial or periodical publication
               such as a journal, magazine, or newspaper
        - 's': (series) the title applies to a series of otherwise distinct publications
               such as a collection
        - 'u': (unpublished) the title applies to any unpublished material
               (including theses and dissertations unless published by a commercial press)
        """
        assert level in ['m', 'a', 'j', 's', 'u']
        for title in self.tree.xpath('//tei:sourceDesc/tei:biblFull/tei:titleStmt/tei:title', namespaces=NS):
            title.set("level", level)

    def add_author(self, person, typ):
        """
        Add an author to the title statements.
        """
        author = etree.Element("%sauthor" % TEI)
        if typ == "personal":
            pers_name = etree.SubElement(author, "%spersName" % TEI)
            for key in person:
                if key == "family":
                    surname = etree.SubElement(pers_name, "%ssurname" % TEI)
                    surname.text = person[key]
                elif key == "given":
                    forename = etree.SubElement(pers_name, "%sforename" % TEI)
                    forename.text = person[key]
                elif key == "date" or key == "unspecified":
                    continue
                else:
                    add_name = etree.SubElement(pers_name, "%saddName" % TEI)
                    add_name.text = person[key]
        elif typ == "corporate":
            org_name = etree.SubElement(author, "%sorgName" % TEI)
            org_name.text = " ".join(person[key] for key in person)
        for title_stmt in self.tree.xpath('//tei:titleStmt', namespaces=NS):
            title_stmt.append(copy.deepcopy(author))

    def add_note(self, note):
        """
        Add a note with details about the document.
        """
        fileDesc = self.tree.xpath('//tei:fileDesc', namespaces=NS)[0]
        if not fileDesc.xpath('/tei:notesStmt', namespaces=NS):
            notes = etree.SubElement(fileDesc, "%snotesStmt" % TEI)
        else:
            notes = fileDesc.xpath('/tei:notesStmt', namespaces=NS)[0]
        node = etree.SubElement(notes, "%snote" % TEI)
        node.text = note
        node.set("type", "remarkDocument")

    def add_place(self, place):
        """
        Add a publication place to the publication statement.
        """
        publication_stmt = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt', namespaces=NS)[0]
        pub_place = etree.SubElement(publication_stmt, "%spubPlace" % TEI)
        for key in place:
            if key == "text":
                pub_place.text = place[key]
            elif key == "code":
                pub_place.set("corresp", place[key])

    def add_date(self, date):
        """
        Add a publication date to the publication statement.
        """
        publication_stmt = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt', namespaces=NS)[0]
        for key in date:
            pub_date = etree.SubElement(publication_stmt, "%sdate" % TEI)
            pub_date.set("type", "publication")
            pub_date.text = date[key]
            if key != "unspecified":
                pub_date.set("datingPoint", key)

    def add_publisher(self, publisher):
        """
        Adds a publisher to the publication statement.
        """
        publication_stmt = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt', namespaces=NS)[0]
        publisher_node = etree.Element("%spublisher" % TEI)
        name = etree.SubElement(publisher_node, "%sname" % TEI)
        name.text = publisher
        publication_stmt.insert(0, publisher_node)

    def add_source_edition(self, manuscript_edition):
        """
        Add an edition statement with details on the source manuscript.
        """
        bibl_full = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull', namespaces=NS)[0]
        edition_stmt = etree.SubElement(bibl_full, "%seditionStmt" % TEI)
        edition = etree.SubElement(edition_stmt, "%sedition" % TEI)
        edition.text = manuscript_edition

    def add_digital_edition(self, digital_edition):
        """
        Add an edition statement with details on the digital edition.
        """
        title_stmt = self.tree.xpath('//tei:fileDesc', namespaces=NS)[0]
        edition_stmt = etree.SubElement(title_stmt, "%seditionStmt" % TEI)
        edition = etree.SubElement(edition_stmt, "%sedition" % TEI)
        edition.text = digital_edition

    def add_hoster(self, hoster):
        """
        Add a publisher of the digital edition
        """
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=NS)[0]
        publisher = etree.SubElement(publication_stmt, "%spublisher" % TEI)
        publisher.text = hoster

    def set_availability(self, status, licence_text, licence_url):
        """
        Set the availability conditions of the digital edition
        """
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=NS)[0]
        availability = publication_stmt.find('%savailability' % TEI)
        if availability is not None:
            availability.clear()
        else:
            availability = etree.SubElement(publication_stmt, "%savailability" % TEI)

        licence = etree.SubElement(availability, "%slicence" % TEI)
        if licence_url != "":
            licence.set("target", licence_url)
        # an explicit licence has been set
        if status == "licence" and licence_text != "":
            availability.set("status", "licenced")
            licence.text = licence_text
        # public domain
        elif status == "free":
            licence.text = "In the public domain"
            availability.set("status", "free")
        elif status == "unknown":
            availability.set("status", "unknown")
        # use restricted as default
        else:
            availability.set("status", "restricted")
            licence.text = "Available under licence from the publishers."

    def add_encoding_date(self, date):
        """
        Add the date of encoding for the digital edition
        """
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=NS)[0]
        encoding_date = etree.SubElement(publication_stmt, "%sdate" % TEI)
        encoding_date.set("type", "publication")
        if date:
            encoding_date.text = date

    def set_encoding_description(self, creator):
        """
        Set some details on the encoding of the digital edition
        """
        encoding_desc = self.tree.xpath('//tei:encodingDesc', namespaces=NS)[0]
        if creator:
            encoding_desc_details = etree.SubElement(encoding_desc, "%sp" % TEI)
            encoding_desc_details.text = "Encoded with the help of %s." % creator

    def add_repository(self, name):
        """
        Add the repository of the (original) manuscript
        """
        ms_ident = self.tree.xpath('//tei:msDesc/tei:msIdentifier', namespaces=NS)[0]
        repository = etree.SubElement(ms_ident, "%srepository" % TEI)
        repository.text = name

    def add_identifier(self, type_, value):
        """
        Add the URN, PURL, VD ID, shelfmark etc. of the digital edition
        """
        ms_ident = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno', namespaces=NS)[0]
        # FIXME: URN, DTAID, ... should go to /tei:fileDesc/tei:publicationStmt/tei:idno instead
        idno = etree.SubElement(ms_ident, "%sidno" % TEI)
        idno.set("type", type_)
        idno.text = value

    def set_type_desc(self, description):
        """
        Set the type description
        """
        phys_desc = self.tree.xpath('//tei:msDesc/tei:physDesc', namespaces=NS)[0]
        type_desc = etree.SubElement(phys_desc, "%stypeDesc" % TEI)
        for line in description.split('\n'):
            par = etree.SubElement(type_desc, "%sp" % TEI)
            par.text = line

    def add_classcode(self, scheme, code):
        """
        Add a document classification code.
        """
        profile_desc = self.tree.xpath('//tei:profileDesc', namespaces=NS)[0]
        if not profile_desc.xpath('/tei:textClass', namespaces=NS):
            textclass = etree.SubElement(profile_desc, "%stextClass" % TEI)
        else:
            textclass = profile_desc.xpath('/tei:textClass', namespaces=NS)[0]
        classcode = etree.SubElement(textclass, "%sclassCode" % TEI)
        classcode.set("scheme", scheme)
        classcode.text = code

    def add_keywords(self, scheme, terms):
        """
        Add a document classification list of terms.
        """
        profile_desc = self.tree.xpath('//tei:profileDesc', namespaces=NS)[0]
        if not profile_desc.xpath('/tei:textClass', namespaces=NS):
            textclass = etree.SubElement(profile_desc, "%stextClass" % TEI)
        else:
            textclass = profile_desc.xpath('/tei:textClass', namespaces=NS)[0]
        keywords = etree.SubElement(textclass, "%skeywords" % TEI)
        keywords.set("scheme", scheme)
        for type_, term in terms:
            node = etree.SubElement(keywords, "%sterm" % TEI)
            node.text = term
            if type_:
                node.set("type", type_)

    def add_language(self, language):
        """
        Add a language of the source document
        """
        lang_usage = self.tree.xpath('//tei:profileDesc/tei:langUsage', namespaces=NS)[0]
        lang = etree.SubElement(lang_usage, "%slanguage" % TEI)
        lang.set("ident", language[0])
        lang.text = language[1]

    def add_extent(self, extent):
        """
        Add information on the extent of the source document
        """
        phys_desc = self.tree.xpath('//tei:msDesc/tei:physDesc', namespaces=NS)[0]
        if not phys_desc.xpath('/tei:objectDesc/tei:supportDesc', namespaces=NS):
            obj_desc = etree.SubElement(phys_desc, "%sobjectDesc" % TEI)
            support_desc = etree.SubElement(obj_desc, "%ssupportDesc" % TEI)
        else:
            support_desc = phys_desc.xpath('/tei:objectDesc/tei:supportDesc', namespaces=NS)[0]
        extent_elem = etree.SubElement(support_desc, "%sextent" % TEI)
        extent_elem.text = extent

    def add_collection(self, collection):
        """
        Add a (free-text) collection of the digital document
        """
        profile_desc = self.tree.xpath('//tei:msDesc/tei:msIdentifier', namespaces=NS)[0]
        coll = etree.SubElement(profile_desc, "%scollection" % TEI)
        coll.text = collection

    def compile_bibl(self, type_):
        """
        Compile the content of the short citation element 'bibl' based on the current state
        """
        if type_:
            self.bibl.set("type", type_)
        bibl_text = ""
        if self.authors:
            bibl_text += "; ".join(self.authors) + ": "
        elif type_ and type_.startswith("M"):
            bibl_text = "[N. N.], "
        bibl_text += self.main_title + "."
        if self.places:
            bibl_text += " " + self.places[0].split(":")[1]
            if len(self.places) > 1:
                bibl_text += " u. a."
        if self.dates:
            if self.places:
                bibl_text += ","
            bibl_text += " " + self.dates[0] + "."
        self.bibl.text = bibl_text

    def add_ocr_text(self, mets):
        """
        Add OCR text from FULLTEXT file group to the single divs
        """
        # the text-holding elements
        front = self.tree.xpath('//tei:front', namespaces=NS)
        body = self.tree.xpath('//tei:body', namespaces=NS)
        back = self.tree.xpath('//tei:back', namespaces=NS)

        if front:
            for node in front[0].iterchildren():
                self.__add_ocr_to_node(node, mets)
        for node in body[0].iterchildren():
            self.__add_ocr_to_node(node, mets)
        if back:
            for node in back[0].iterchildren():
                self.__add_ocr_to_node(node, mets)

    def __add_ocr_to_node(self, node, mets):
        """
        Add text to a given node and recursively add text to children too (post order!)
        """

        node_id = node.get("id")
        self.logger.debug("Adding text for %s", node_id)
        for childnode in node.iterchildren():
            self.__add_ocr_to_node(childnode, mets)
        struct_links = mets.get_struct_links(node_id)
        if not struct_links and node_id in mets.page_map:
            # already physical
            struct_links = [node_id]

        # a header will always be on the first page of a div
        first = True

        retries = Retry(total=3,
                        status_forcelist=[
                            # probably too wide (only transient failures):
                            408, # Request Timeout
                            409, # Conflict
                            412, # Precondition Failed
                            417, # Expectation Failed
                            423, # Locked
                            424, # Fail
                            425, # Too Early
                            426, # Upgrade Required
                            428, # Precondition Required
                            429, # Too Many Requests
                            440, # Login Timeout
                            500, # Internal Server Error
                            503, # Service Unavailable
                            504, # Gateway Timeout
                            509, # Bandwidth Limit Exceeded
                            529, # Site Overloaded
                            598, # Proxy Read Timeout
                            599, # Proxy Connect Timeout
                        ])
        adapter = HTTPAdapter(max_retries=retries)
        # iterate over all struct links for a div
        for struct_link in struct_links:
            alto_link = mets.get_alto(struct_link)
            # only collect ocr from a file once!
            if not alto_link in self.alto_map:
                try:
                    sections = urlparse(alto_link)
                except:
                    continue

                # use urlopen for both paths and URLs
                if not sections.scheme:
                    mod_link = 'file:' + alto_link
                else:
                    mod_link = alto_link
                self.logger.debug(mod_link)

                if mod_link.startswith('file:'):
                    fpath = mod_link[5:]
                    if fpath.startswith('///'):
                        # support condensed file://localhost/path
                        fpath = fpath[3:]
                        if not fpath.startswith('/'):
                            fpath = os.path.join(mets.wd, fpath)
                    elif fpath.startswith('//'):
                        # support non-standard file://path
                        fpath = fpath[2:]
                        fpath = os.path.join(mets.wd, fpath)
                    elif fpath.startswith('/'):
                        # support file:/path
                        fpath = fpath[1:]
                        fpath = os.path.join(mets.wd, fpath)
                    else:
                        fpath = os.path.join(mets.wd, fpath)
                    try:
                        with open(fpath, 'rb') as file:
                            alto = Alto.fromfile(file)
                    except FileNotFoundError as e:
                        self.logger.error("cannot open OCR result for '%s': %s", mod_link, e)
                        continue
                else:
                    with requests.Session() as session:
                        session.mount('http://', adapter)
                        session.mount('https://', adapter)
                        try:
                            response = session.get(mod_link, timeout=3, stream=True)
                        except requests.exceptions.RetryError as e:
                            self.logger.error("cannot fetch OCR result for '%s': %s", mod_link, e)
                            continue
                        alto = Alto.frombytes(response.content)

                # save original link!
                self.alto_map[alto_link] = alto

                pb = etree.SubElement(node, "%spb" % TEI)
                try:
                    pagenum = list(mets.page_map.keys()).index(struct_link)
                except ValueError:
                    self.logger.warning("cannot determine image number for link '%s'", struct_link)
                    pagenum = len(node.xpath("tei:pb", namespaces=NS))
                pageid = "f{:04d}".format(pagenum + 1)
                pb.set("facs", "#" + pageid)
                orderlabel = mets.get_orderlabel(struct_link) or mets.get_order(struct_link)
                if orderlabel:
                    pb.set("n", str(orderlabel))
                if 'page' in self.refs:
                    if self.purl:
                        pb.set("corresp", self.purl + "/" + pageid[1:])
                    img_url = mets.get_img(struct_link)
                    if img_url:
                        facsimile = self.tree.xpath('//tei:facsimile', namespaces=NS)[0]
                        # facsimile.set("base", ...common url_prefix...)
                        # todo: DTABf seems to use "graphic" directly, but other dialects wrap them inside a "surface"
                        graphic = etree.SubElement(facsimile, "%sgraphic" % TEI)
                        mime, enc = mimetypes.guess_type(img_url)
                        if mime is not None:
                            graphic.set("mimeType", mime)
                        graphic.set("url", img_url)
                        graphic.set("id", pageid)
                for text_block in alto.get_text_blocks():
                    p = etree.SubElement(node, "%sp" % TEI)
                    for line in alto.get_lines_in_text_block(text_block):
                        lb = etree.SubElement(p, "%slb" % TEI)
                        if 'line' in self.refs:
                            line_id = line.get("ID")
                            if not line_id:
                                block = line.getparent()
                                line_id = block.get("ID") + '_%04d' % block.index(line)
                            lb.set("n", line_id)
                        line_text = alto.get_text_in_line(line)
                        if line_text:
                            lb.tail = line_text
                            # FIXME: Technically, we only need to index the lines of div-introducing pages
                            alto.text += line_text
                            for i in range(0, len(line_text)):
                                alto.line_index_struct[alto.line_index] = lb
                                alto.line_index += 1
            else:
                alto = self.alto_map[alto_link]
            # find the most likely position of the label on the page
            if first:
                self.logger.debug("Search for '%s' on page '%s'" % (node.get("rend", default=""), str(alto_link)))
                label = node.get("rend", default="")
                if len(label) and alto.text and label != "Text":
                    begin, length = alto.get_best_insert_index(label, True)
                    pars, lines = alto.collect_text_nodes(begin, length)

                    # par → head
                    # split into head and non-head content
                    if len(pars[0]) > len(lines):
                        argument = etree.Element("%sargument" % TEI)
                        par_pre = etree.SubElement(argument, "%sp" % TEI)
                        par_post = etree.Element("%sp" % TEI)
                        status = 0
                        for line in pars[0]:
                            if line == lines[0]:
                                status += 1
                            if line == lines[-1]:
                                status += 1
                            elif status == 0:
                                par_pre.append(line)
                            elif status == 2:
                                par_post.append(line)
                        if len(par_pre) > 0:
                            pars[0].getparent().insert(pars[0].getparent().index(pars[0]), argument)
                        if len(par_post) > 0:
                            pars[0].getparent().insert(pars[0].getparent().index(pars[0]) + 1, par_post)
                    pars[0].tag = "%shead" % TEI
                    # realize correct div assigment in cases where a structure does not start a page
                    if pars[0].getparent().get("id") != node.get("id"):
                        self.logger.debug("Replace head for div %s (%s)" % (node.get("id"), node.get("rend")))
                        for par in reversed(pars[0].getparent()[pars[0].getparent().index(pars[0]):]):
                            node.insert(0, par)
            first = False

    def add_div_structure(self, div):
        """
        Add logical div elements to the text font/body/back according to the given div hierarchy
        """

        # div structure has to be added to text
        front = self.tree.xpath('//tei:front', namespaces=NS)[0]
        body = self.tree.xpath('//tei:body', namespaces=NS)[0]
        back = self.tree.xpath('//tei:back', namespaces=NS)[0]

        # descend to the deepest AMD
        while div.get_ADMID() is None:
            self.logger.debug("Found logical outer div type %s: %s", div.get_TYPE(), div.get_ID())
            div = div.get_div()[0]
        # we want to dive into multivolume_work, periodical, newspaper, year, month...
        # we are looking for issue, volume, monograph, lecture, dossier, act, judgement, study, paper, *_thesis, report, register, file, fragment, manuscript...
        start_div = div
        while start_div.get_div() and start_div.get_div()[0].get_ADMID() is not None:
            self.logger.debug("Found logical inner div type %s: %s", start_div.get_TYPE(), start_div.get_ID())
            div = start_div
            start_div = start_div.get_div()[0]

        # start search
        has_frontmatter = (any(1 for sub_div in div.get_div()
                               if sub_div.get_TYPE() in [
                                       # FIXME: what are the exact criteria for the presence of front-matter in DFG METS?
                                       "title_page",
                                       "preface",
                                       "dedication",
                                       "engraved_titlepage",
                               ]) and
                           # no front if document has multiple title_page (e.g. multiple contained_work):
                           not sum(1 for sub_div in div.get_div()
                                   if sub_div.get_TYPE() == "title_page") > 1)
        entry_point = front if has_frontmatter else body
        for sub_div in div.get_div():
            subtype = sub_div.get_TYPE() or sub_div.get_LABEL() or sub_div.get_ORDERLABEL() or ""
            divtype = DIV_METS2TEI.get(subtype.lower(), "")
            if (subtype == "binding" or
                subtype == "colour_checker" or
                subtype == "spine" or
                subtype == "paste_down" or
                subtype == "endsheet" or
                subtype.startswith("cover")):
                continue
            elif entry_point is front and subtype == "title_page":
                self.__add_div(entry_point, sub_div, 1, tag="titlePage")
            else:
                if has_frontmatter and entry_point is front and subtype in [
                        # FIXME: what are the exact criteria for the end of front-matter in DFG METS?
                        "article",
                        "chapter",
                        "section",
                        "part",
                        "fascicle",
                        "other",
                        ]:
                    entry_point = body
                elif entry_point is body and subtype in [
                        # FIXME: what are the exact criteria for the start of back-matter in DFG METS?
                        "epilogue",
                        "index",
                        "corrigenda",
                        #"contents", # can also be in front
                        "imprint",
                        "dedication",
                        "appendix",
                        "additional",
                        "attached_work",
                ]:
                    entry_point = back
                self.__add_div(entry_point, sub_div, 1, divtype=divtype)

    def add_physical_pages(self, pages):
        """
        Add logical div elements to the text font/body/back according to the given div hierarchy
        """

        # div structure has to be added to text
        body = self.tree.xpath('//tei:body', namespaces=NS)[0]

        for page in pages:
            self.logger.debug("Found physical page %s", page.get_ID())
            self.__add_div(body, page, 1)

    def __add_div(self, insert_node, div, n, tag="div", divtype=""):
        """
        Add div element to a given node and recursively add children too
        """
        div_id = div.get_ID()
        new_div = etree.SubElement(insert_node, "%s%s" % (TEI, tag))
        new_div.set("id", div_id)
        label = div.get_LABEL()
        if label:
            new_div.set("n", str(n))
            #head = etree.SubElement(new_div, "%s%s" % (TEI, "head"))
            #head.text = label
            new_div.set("rend", label)
        if tag == "div" and divtype:
            new_div.set("type", divtype)
        self.logger.debug("Adding %s[@id=%s,@n=%d%s%s] for %s",
                          tag, div_id, n,
                          ",@rend=%s" % label if label else "",
                          ",@type=%s" % divtype if divtype else "",
                          insert_node.tag.split('}')[-1])
        for sub_div in div.get_div():
            subtype = sub_div.get_TYPE() or sub_div.get_LABEL() or sub_div.get_ORDERLABEL() or ""
            self.__add_div(new_div, sub_div, n+1, divtype=DIV_METS2TEI.get(subtype.lower(), ""))

