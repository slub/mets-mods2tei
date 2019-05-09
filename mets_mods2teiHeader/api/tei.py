# -*- coding: utf-8 -*-

from lxml import etree

import os

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
        self.tree.xpath('//tei:titleStmt/tei:title[@type="main"]', namespaces=ns)[0].text = string

    def add_sub_title(self, string):
        """
        Adds a sub title to the title statement.
        """
        title_stmt = self.tree.xpath('//tei:titleStmt', namespaces=ns)[0]
        sub_title = etree.SubElement(title_stmt, "title")
        sub_title.set("type", "sub")
        sub_title.text = string

    def add_author(self, person, typ):
        """
        Adds an author to the title statement.
        """
        title_stmt = self.tree.xpath('//tei:titleStmt', namespaces=ns)[0]
        author = etree.SubElement(title_stmt, "author")
        if typ == "personal":
            pers_name = etree.SubElement(author, "persName")
            for key in person:
                if key == "family":
                    surname = etree.SubElement(pers_name, "surname")
                    surname.text = person[key]
                elif key == "given":
                    forename = etree.SubElement(pers_name, "forename")
                    forename.text = person[key]
                else:
                    add_name = etree.SubElement(pers_name, "addName")
                    add_name.text = person[key]
        elif typ == "corporate":
            org_name = etree.SubElement(author, "orgName")
            org_name.text = " ".join(person[key] for key in person)

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
