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

    def tostring(self):
        """
        Serializes the TEI object as xml string.
        """
        return etree.tostring(self.tree, encoding="utf-8")

    def get_main_title(self):
        """
        Returns the main title of the work represented
        by the TEI Header.
        """
        return self.tree.xpath('//tei:titleStmt/tei:title[@type="main"]', namespaces=ns)[0].text

    def set_main_title(self, string):
        """
        Sets the main title of the title statement.
        """
        for main_title in self.tree.xpath('//tei:titleStmt/tei:title[@type="main"]', namespaces=ns):
            main_title.text = string

    def add_sub_title(self, string):
        """
        Adds a sub title to the title statement.
        """
        sub_title = etree.Element("title")
        sub_title.set("type", "sub")
        sub_title.text = string
        for title_stmt in self.tree.xpath('//tei:titleStmt', namespaces=ns):
            title_stmt.append(copy.deepcopy(sub_title))

    def add_author(self, person, typ):
        """
        Adds an author to the title statement.
        """
        author = etree.Element("author")
        if typ == "personal":
            pers_name = etree.SubElement(author, "persName")
            for key in person:
                if key == "family":
                    surname = etree.SubElement(pers_name, "surname")
                    surname.text = person[key]
                elif key == "given":
                    forename = etree.SubElement(pers_name, "forename")
                    forename.text = person[key]
                elif key == "date" or key == "unspecified":
                    continue
                else:
                    add_name = etree.SubElement(pers_name, "addName")
                    add_name.text = person[key]
        elif typ == "corporate":
            org_name = etree.SubElement(author, "orgName")
            org_name.text = " ".join(person[key] for key in person)
        for title_stmt in self.tree.xpath('//tei:titleStmt', namespaces=ns):
            title_stmt.append(copy.deepcopy(author))

    def add_place(self, place):
        """
        Adds a publication place to the publication statement.
        """
        publication_stmt = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt', namespaces=ns)[0]
        pub_place = etree.SubElement(publication_stmt, "pubPlace")
        for key in place:
            if key == "text":
                pub_place.text = place[key]
            elif key == "code":
                pub_place.set("corresp", place[key])

    def add_date(self, date):
        """
        Adds a publication date to the publication statement.
        """
        publication_stmt = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt', namespaces=ns)[0]
        for key in date:
            pub_date = etree.SubElement(publication_stmt, "date")
            pub_date.set("type", "publication")
            pub_date.text = date[key]
            if key != "unspecified":
                pub_date.set("datingPoint", key)

    def add_publisher(self, publisher):
        """
        Adds a publisher to the publication statement.
        """
        publication_stmt = self.tree.xpath('//tei:fileDesc/tei:sourceDesc/tei:biblFull/tei:publicationStmt', namespaces=ns)[0]
        publisher_node = etree.Element("publisher")
        name = etree.SubElement(publisher_node, "name")
        name.text = publisher
        publication_stmt.insert(0, publisher_node)

    def add_digital_edition(self, digital_edition):
        """
        Adds an edition statement with details on the digital edition.
        """
        title_stmt = self.tree.xpath('//tei:titleStmt', namespaces=ns)[0]
        edition_stmt = etree.SubElement(title_stmt, "editionStmt")
        edition = etree.SubElement(edition_stmt, "edition")
        edition.text = digital_edition

    def set_hoster(self, hoster):
        """
        Set the publisher of the digital edition
        """
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=ns)[0]
        publisher = etree.SubElement(publication_stmt, "publisher")
        publisher.text = hoster

    def set_availability(self, status, licence_text, licence_url):
        """
        Set the availability conditions of the digital edition
        """
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=ns)[0]
        availability = etree.SubElement(publication_stmt, "availability")
        
        # an explicit licence has been set
        if status == "licence" and licence_text != "":
            licence = etree.SubElement(availability, "licence")
            licence.text = licence_text
            if licence_url != "":
                licence.set("target", licence_url)
        # public domain
        elif status == "free":
            note = etree.SubElement(availability, "p")
            note.text = "In the public domain"
            availability.set("status", "free")
        elif status == "unknown":
            availability.set("status", "unknown")
        # use restricted as default
        else:
            availability.set("status", "restricted")
            note = etree.SubElement(availability, "p")
            note.text = "Available under licence from the publishers."

    def set_encoding_date(self, date):
        """
        Set the date of encoding for the digital edition
        """
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=ns)[0]
        encoding_date = etree.SubElement(publication_stmt, "date")
        encoding_date.set("type", "publication")
        encoding_date.text = date

    def set_encoding_description(self, creator):
        """
        Sets some details on the encoding of the digital edition
        """
        encoding_desc = self.tree.xpath('//tei:encodingDesc', namespaces=ns)[0]
        encoding_desc_details = etree.SubElement(encoding_desc, "p")
        encoding_desc_details.text = "Encoded with the help of %s." % creator
