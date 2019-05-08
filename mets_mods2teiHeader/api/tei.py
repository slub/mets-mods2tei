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
        # adjust dummy author
        title_stmt = self.tree.xpath('//tei:titleStmt', namespaces=ns)[0]
        author = title_stmt.xpath('tei:author', namespaces=ns)[0]
        if author.text.strip():
            author = etree.SubElement(title_stmt, "author")
        if typ == "personal":
            pers_name = etree.SubElement(author, "persName")
        else:
            pers_name = etree.SubElement(author, "orgName")
        pers_name.text = " ".join(person[key] for key in person)
