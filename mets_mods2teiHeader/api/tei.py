# -*- coding: utf-8 -*-

from lxml import etree

import os

import copy

from pkg_resources import resource_filename, Requirement

ns = {
     'tei': "http://www.tei-c.org/ns/1.0",
}
TEI = "{%s}" % ns['tei']

class Tei:

    def __init__(self):
        """
        The constructor.
        """

        self.tree = etree.parse(os.path.realpath(resource_filename(Requirement.parse("mets_mods2teiHeader"), 'mets_mods2teiHeader/data/tei_skeleton.xml')))

        self.alto_map = {}

    def tostring(self):
        """
        Serializes the TEI object as xml string.
        """
        return etree.tostring(self.tree, encoding="utf-8")

    def fill_from_mets(self, mets):
        """
        Fill the contents of the TEI object from a METS instance
        """

        #
        # replace skeleton values by real ones

        # main title
        self.set_main_title(mets.get_main_title())

        # publication level
        self.set_publication_level(mets.type)

        # sub titles
        for sub_title in mets.get_sub_titles():
            self.add_sub_title(sub_title)

        # authors
        for typ, author in mets.get_authors():
            self.add_author(author,typ)

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
        if mets.get_owner_manuscript():
            self.add_repository(mets.get_owner_manuscript())

        # shelf locator
        for shelf_locator in mets.get_shelf_locators():
            self.add_shelfmark(shelf_locator)

        # identifiers
        if mets.get_identifiers():
            self.add_identifiers(mets.get_identifiers())

        # type description
        if mets.get_scripts():
            self.set_type_desc('\n'.join(script for script in mets.get_scripts()))

        # languages
        for ident_name in mets.get_languages().items():
            self.add_language(ident_name)

        # extents
        for extent in mets.extents:
            self.add_extent(extent)

        # collection
        for collection in mets.collections:
            self.add_collection(collection)

        #
        # citation
        self.compile_bibl()

        #
        # text part

        # div structure
        self.add_div_structure(mets.get_div_structure())

        # OCR
        self.add_ocr_text(mets)

    @property
    def main_title(self):
        """
        Return the main title of the work represented
        by the TEI Header.
        """
        return self.tree.xpath('//tei:titleStmt/tei:title[@type="main"]', namespaces=ns)[0].text
    
    @property
    def publication_level(self):
        """
        Return the level of publication ('monographic' vs. 'analytic')
        """
        return self.tree.xpath('//tei:sourceDesc/tei:biblFull/tei:titleStmt/tei:title[@type="main"]', namespaces=ns)[0].get("level")

    @property
    def subtitles(self):
        """
        Return information on the subtitle(s) of the work represented
        by the TEI Header.
        """
        return [subtitle.text for subtitle in self.tree.xpath('//tei:fileDesc/tei:titleStmt/tei:title[@type="sub"]', namespaces=ns)]

    @property
    def authors(self):
        """
        Return information on the author(s) of the work represented
        by the TEI Header.
        """
        authors = []
        for author in self.tree.xpath('//tei:fileDesc/tei:titleStmt/tei:author', namespaces=ns):
            authors.append(", ".join(author.xpath('descendant-or-self::*/text()')))
        return authors

    @property
    def dates(self):
        """
        Return information on the publication date(s) of the work represented
        by the TEI Header.
        """
        return [date.text for date in self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt/tei:date', namespaces=ns)]

    @property
    def places(self):
        """
        Return information on the publication place(s) of the work represented
        by the TEI Header.
        """
        return ["%s:%s" % (place.get("corresp"), place.text) for place in self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt/tei:pubPlace', namespaces=ns)]

    @property
    def publishers(self):
        """
        Return information on the publishers of the source work represented
        by the TEI Header.
        """
        return [publisher.text for publisher in self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt/tei:publisher/tei:name', namespaces=ns)]

    @property
    def hosters(self):
        """
        Return information on the publishers of the digitalized work represented
        by the TEI Header.
        """
        return [publisher.text for publisher in self.tree.xpath('//tei:fileDesc/tei:publicationStmt/tei:publisher', namespaces=ns)]

    @property
    def source_editions(self):
        """
        Return information on the editions of the source work represented
        by the TEI Header.
        """
        return [source_edition.text for source_edition in self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:editionStmt/tei:edition', namespaces=ns)]

    @property
    def digital_editions(self):
        """
        Return information on the editions of the digitalized work represented
        by the TEI Header.
        """
        return [digital_edition.text for digital_edition in self.tree.xpath('//tei:fileDesc/tei:titleStmt/tei:editionStmt/tei:edition', namespaces=ns)]

    @property
    def encoding_dates(self):
        """
        Return information on the publishing dates of the digitalized work represented
        by the TEI Header.
        """
        return ["%s:%s" % (encoding_date.get("type"), encoding_date.text) for encoding_date in self.tree.xpath('//tei:fileDesc/tei:publicationStmt/tei:date', namespaces=ns)]

    @property
    def extents(self):
        """
        Return information on the extent of the work represented
        by the TEI Header.
        """
        return [extent.text for extent in self.tree.xpath('//tei:msDesc/tei:physDesc/tei:objectDesc/tei:supportDesc/tei:extent', namespaces=ns)]

    @property
    def collections(self):
        """
        Return information on the collections of the work represented
        by the TEI Header.
        """
        return [collection.text for collection in self.tree.xpath('//tei:profileDesc/tei:creation', namespaces=ns)]

    @property
    def bibl(self):
        """
        Return the short citation of the work represented
        by the TEI Header.
        """
        return self.tree.xpath("//tei:fileDesc/tei:sourceDesc/tei:bibl", namespaces=ns)[0]

    def set_main_title(self, string):
        """
        Set the main title of the title statements.
        """
        for main_title in self.tree.xpath('//tei:titleStmt/tei:title[@type="main"]', namespaces=ns):
            main_title.text = string

    def set_publication_level(self, level):
        """
        Set the level of publication ('monographic' vs. 'analytic')
        """
        self.tree.xpath('//tei:sourceDesc/tei:biblFull/tei:titleStmt/tei:title[@type="main"]', namespaces=ns)[0].set("level", level)

    def add_sub_title(self, string):
        """
        Add a sub title to the title statements.
        """
        sub_title = etree.Element("%stitle" % TEI)
        sub_title.set("type", "sub")
        sub_title.text = string
        for title_stmt in self.tree.xpath('//tei:titleStmt', namespaces=ns):
            title_stmt.append(copy.deepcopy(sub_title))

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
        for title_stmt in self.tree.xpath('//tei:titleStmt', namespaces=ns):
            title_stmt.append(copy.deepcopy(author))

    def add_place(self, place):
        """
        Add a publication place to the publication statement.
        """
        publication_stmt = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt', namespaces=ns)[0]
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
        publication_stmt = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt', namespaces=ns)[0]
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
        publication_stmt = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt', namespaces=ns)[0]
        publisher_node = etree.Element("%spublisher" % TEI)
        name = etree.SubElement(publisher_node, "%sname" % TEI)
        name.text = publisher
        publication_stmt.insert(0, publisher_node)

    def add_source_edition(self, manuscript_edition):
        """
        Add an edition statement with details on the source manuscript.
        """
        bibl_full = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull', namespaces=ns)[0]
        edition_stmt = etree.SubElement(bibl_full, "%seditionStmt" % TEI)
        edition = etree.SubElement(edition_stmt, "%sedition" % TEI)
        edition.text = manuscript_edition

    def add_digital_edition(self, digital_edition):
        """
        Add an edition statement with details on the digital edition.
        """
        title_stmt = self.tree.xpath('//tei:titleStmt', namespaces=ns)[0]
        edition_stmt = etree.SubElement(title_stmt, "%seditionStmt" % TEI)
        edition = etree.SubElement(edition_stmt, "%sedition" % TEI)
        edition.text = digital_edition

    def add_hoster(self, hoster):
        """
        Add a publisher of the digital edition
        """
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=ns)[0]
        publisher = etree.SubElement(publication_stmt, "%spublisher" % TEI)
        publisher.text = hoster

    def set_availability(self, status, licence_text, licence_url):
        """
        Set the availability conditions of the digital edition
        """
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=ns)[0]
        availability = etree.SubElement(publication_stmt, "%savailability" % TEI)
        
        # an explicit licence has been set
        if status == "licence" and licence_text != "":
            licence = etree.SubElement(availability, "%slicence" % TEI)
            licence.text = licence_text
            if licence_url != "":
                licence.set("target", licence_url)
        # public domain
        elif status == "free":
            note = etree.SubElement(availability, "%sp" % TEI)
            note.text = "In the public domain"
            availability.set("status", "free")
        elif status == "unknown":
            availability.set("status", "unknown")
        # use restricted as default
        else:
            availability.set("status", "restricted")
            note = etree.SubElement(availability, "%sp" % TEI)
            note.text = "Available under licence from the publishers."

    def add_encoding_date(self, date):
        """
        Add the date of encoding for the digital edition
        """
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=ns)[0]
        encoding_date = etree.SubElement(publication_stmt, "%sdate" % TEI)
        encoding_date.set("type", "publication")
        encoding_date.text = date

    def set_encoding_description(self, creator):
        """
        Set some details on the encoding of the digital edition
        """
        encoding_desc = self.tree.xpath('//tei:encodingDesc', namespaces=ns)[0]
        encoding_desc_details = etree.SubElement(encoding_desc, "%sp" % TEI)
        encoding_desc_details.text = "Encoded with the help of %s." % creator

    def add_repository(self, repository):
        """
        Adds the repository of the (original) manuscript
        """
        ms_ident = self.tree.xpath('//tei:msDesc/tei:msIdentifier', namespaces=ns)[0]
        repository_node = etree.SubElement(ms_ident, "%srepository" % TEI)
        repository_node.text = repository

    def add_shelfmark(self, shelfmark):
        """
        Add the shelf mark of the (original) manuscript
        """
        ms_ident_idno = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno', namespaces=ns)[0]
        idno = etree.SubElement(ms_ident_idno, "%sidno" % TEI)
        idno.set("type", "shelfmark")
        idno.text = shelfmark

    def add_identifiers(self, identifiers):
        """
        Adds the identifiers of the digital edition
        """
        ms_ident_idno = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno', namespaces=ns)[0]
        for identifier in identifiers:
            idno = etree.SubElement(ms_ident_idno, "%sidno" % TEI)
            idno.set("type", identifier[0])
            idno.text = identifier[1]

    def set_type_desc(self, description):
        """
        Set the type description
        """
        phys_desc = self.tree.xpath('//tei:msDesc/tei:physDesc', namespaces=ns)[0]
        type_desc = etree.SubElement(phys_desc, "%stypeDesc" % TEI)
        for line in description.split('\n'):
            par = etree.SubElement(type_desc, "%sp" % TEI)
            par.text = line

    def add_language(self, language):
        """
        Add a language of the source document
        """
        lang_usage = self.tree.xpath('//tei:profileDesc/tei:langUsage', namespaces=ns)[0]
        lang = etree.SubElement(lang_usage, "%slanguage" % TEI)
        lang.set("ident", language[0])
        lang.text = language[1]

    def add_extent(self, extent):
        """
        Add information on the extent of the source document
        """
        phys_desc = self.tree.xpath('//tei:msDesc/tei:physDesc', namespaces=ns)[0]
        if not phys_desc.xpath('/tei:objectDesc/tei:supportDesc', namespaces=ns):
            obj_desc = etree.SubElement(phys_desc, "%sobjectDesc" % TEI)
            support_desc = etree.SubElement(obj_desc, "%ssupportDesc" % TEI)
        else:
            support_desc = phys_desc.xpath('/tei:objectDesc/tei:supportDesc', namespaces=ns)[0]
        extent_elem = etree.SubElement(support_desc, "%sextent" % TEI)
        extent_elem.text = extent

    def add_collection(self, collection):
        """
        Add a (free-text) collection of the digital document
        """
        profile_desc = self.tree.xpath('//tei:profileDesc', namespaces=ns)[0]
        creation = etree.SubElement(profile_desc, "%screation" % TEI)
        creation.text = collection

    def compile_bibl(self):
        """
        Compile the content of the short citation element 'bibl' based on the current state
        """
        if self.publication_level:
            self.bibl.set("type", self.publication_level)
        bibl_text = ""
        if self.authors:
            bibl_text += "; ".join(self.authors) + ": "
        elif self.publication_level == "monograph":
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
        front = self.tree.xpath('//tei:front', namespaces=ns)
        body = self.tree.xpath('//tei:body', namespaces=ns)
        back = self.tree.xpath('//tei:back', namespaces=ns)

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
        
        for childnode in node.iterchildren():
            self.__add_ocr_to_node(childnode, mets)
        altos = mets.get_alto(node.get("id"))
        for alto in altos:
            pass
            #print(etree.tostring(alto))


    def add_div_structure(self, div):
        """
        Add div elements to the text body according to the given list of divs
        """

        # div structure has to be added to text
        text = self.tree.xpath('//tei:text', namespaces=ns)[0]

        # do not add front node to unstructured volumes
        if div.get_div():
            front = etree.SubElement(text, "%sfront" % TEI)

        # body must be present
        body = etree.SubElement(text, "%sbody" % TEI)

        # do not add back node to unstructured volumes
        if div.get_div():
            back = etree.SubElement(text, "%sback" % TEI)
        else:
            # default div for unstructured volumes
            body = etree.SubElement(body, "%sdiv" % TEI)

        for sub_div in div.get_div():
            if sub_div.get_TYPE() == "title_page":
                self.__add_div(front, sub_div, 1, "titlePage")
            elif sub_div.get_TYPE() == "chapter" or sub_div.get_TYPE() == "section":
                self.__add_div(body, sub_div, 1)

    def __add_div(self, insert_node, div, n, tag="div"):
        """
        Add div element to a given node and recursively add children too
        """
        new_div = etree.SubElement(insert_node, "%s%s" % (TEI, tag))
        new_div.set("id", div.get_ID())
        if div.get_LABEL():
            new_div.set("n", str(n))
            new_div.set("rend", div.get_LABEL())
        for sub_div in div.get_div():
            self.__add_div(new_div, sub_div, n+1)

