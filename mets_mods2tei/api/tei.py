# -*- coding: utf-8 -*-

from lxml import etree

import os
import logging
import copy

from contextlib import closing
from urllib.request import urlopen
from urllib.parse import urlparse
from pkg_resources import resource_filename, Requirement

from .alto import Alto

ns = {
     'tei': "http://www.tei-c.org/ns/1.0",
     'alto': "http://www.loc.gov/standards/alto/ns-v2#",
}
TEI = "{%s}" % ns['tei']
ALTO = "{%s}" % ns['alto']

class Tei:

    def __init__(self):
        """
        The constructor.
        """

        self.tree = etree.parse(os.path.realpath(resource_filename(Requirement.parse("mets_mods2tei"), 'mets_mods2tei/data/tei_skeleton.xml')))

        self.alto_map = {}

        # logging
        self.logger = logging.getLogger(__name__)

    def tostring(self):
        """
        Serializes the TEI object as xml string.
        """
        return etree.tostring(self.tree, encoding="utf-8")

    def fill_from_mets(self, mets, ocr=True):
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
        if mets.get_urn():
            self.add_urn(mets.get_urn())
        if mets.get_vd_id():
            self.add_vd_id(mets.get_vd_id())

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
        if ocr:
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
    def availability(self):
        """
        Return information on the availability status represented
        by the TEI Header.
        """
        return self.tree.xpath('//tei:fileDesc/tei:publicationStmt/tei:availability', namespaces=ns)[0].get("status")

    @property
    def licence(self):
        """
        Return information on the licencing conditions represented
        by the TEI Header.
        """
        licence = self.tree.xpath('//tei:fileDesc/tei:publicationStmt/tei:availability/tei:licence', namespaces=ns)
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
    def encoding_description(self):
        """
        Return information on the manners of creation of the digitalized work represented
        by the TEI Header.
        """
        return "".join(self.tree.xpath('//tei:encodingDesc', namespaces=ns)[0].itertext()).strip()

    @property
    def repositories(self):
        """
        Return information on the repositories storing the work represented
        by the TEI Header.
        """
        return [repository.text for repository in self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:repository', namespaces=ns)]

    @property
    def shelfmarks(self):
        """
        Return information on the TEI-Header-represented work's (library) shelfmarks.
        """
        return [shelfmark.text for shelfmark in self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno/tei:idno[@type="shelfmark"]', namespaces=ns)]

    @property
    def urn(self):
        """
        Return information on the TEI-Header-represented work's URN.
        """
        urn = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno/tei:idno[@type="URN"]', namespaces=ns)
        if urn:
            return urn[0].text
        else:
            return ""

    @property
    def vd_id(self):
        """
        Return information on the TEI-Header-represented work's VD ID.
        """
        vd_id = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno/tei:idno[@type="VD"]', namespaces=ns)
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
        publication_stmt = self.tree.xpath('//tei:publicationStmt', namespaces=ns)[0]
        encoding_date = etree.SubElement(publication_stmt, "%sdate" % TEI)
        encoding_date.set("type", "publication")
        if date:
            encoding_date.text = date

    def set_encoding_description(self, creator):
        """
        Set some details on the encoding of the digital edition
        """
        encoding_desc = self.tree.xpath('//tei:encodingDesc', namespaces=ns)[0]
        if creator:
            encoding_desc_details = etree.SubElement(encoding_desc, "%sp" % TEI)
            encoding_desc_details.text = "Encoded with the help of %s." % creator

    def add_repository(self, repository):
        """
        Add the repository of the (original) manuscript
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

    def add_urn(self, urn):
        """
        Add the URN of the digital edition
        """
        ms_ident_idno = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno', namespaces=ns)[0]
        idno = etree.SubElement(ms_ident_idno, "%sidno" % TEI)
        idno.set("type", "URN")
        idno.text = urn

    def add_vd_id(self, vd_id):
        """
        Add the VD ID of the digital edition
        """
        ms_ident_idno = self.tree.xpath('//tei:msDesc/tei:msIdentifier/tei:idno', namespaces=ns)[0]
        idno = etree.SubElement(ms_ident_idno, "%sidno" % TEI)
        idno.set("type", "VD")
        idno.text = vd_id

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
        struct_links = mets.get_struct_links(node.get("id"))
        
        # a header will always be on the first page of a div
        first = True

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

                with closing(urlopen(mod_link)) as f:
                    alto = Alto.read(f)

                # save original link!
                self.alto_map[alto_link] = alto

                pb = etree.SubElement(node, "%spb" % TEI)
                pb.set("facs", "#f{:04d}".format(int(mets.get_order(struct_link))))
                pb.set("corresp", mets.get_img(struct_link))

                for text_block in alto.get_text_blocks():
                    p = etree.SubElement(node, "%sp" % TEI)
                    for line in alto.get_lines_in_text_block(text_block):
                        lb = etree.SubElement(p, "%slb" % TEI)
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
        Add div elements to the text body according to the given list of divs
        """

        # div structure has to be added to text
        text = self.tree.xpath('//tei:text', namespaces=ns)[0]

        # decent to the deepest AMD
        while div.get_ADMID() is None:
            div = div.get_div()[0]
        start_div = div.get_div()[0]
        while start_div.get_div() and start_div.get_div()[0].get_ADMID() is not None:
            div = start_div
            start_div = start_div.get_div()[0]
        
        front = etree.SubElement(text, "%sfront" % TEI)
        body = etree.SubElement(text, "%sbody" % TEI)
        back = etree.SubElement(text, "%sback" % TEI)

        entry_point = front

        for sub_div in div.get_div():
            if sub_div.get_TYPE() == "binding" or sub_div.get_TYPE() == "colour_checker":
                continue
            elif sub_div.get_TYPE() == "title_page":
                self.__add_div(entry_point, sub_div, 1, "titlePage")
            else:
                entry_point = body
                self.__add_div(entry_point, sub_div, 1)

    def __add_div(self, insert_node, div, n, tag="div"):
        """
        Add div element to a given node and recursively add children too
        """
        new_div = etree.SubElement(insert_node, "%s%s" % (TEI, tag))
        new_div.set("id", div.get_ID())
        if div.get_LABEL():
            new_div.set("n", str(n))
            #head = etree.SubElement(new_div, "%s%s" % (TEI, "head"))
            #head.text = div.get_LABEL()
            new_div.set("rend", div.get_LABEL())
        for sub_div in div.get_div():
            self.__add_div(new_div, sub_div, n+1)

