# -*- coding: utf-8 -*-

from lxml import etree

import os
import logging
import re
import Levenshtein

ns = {
     'xlink' : "http://www.w3.org/1999/xlink",
     'alto': "http://www.loc.gov/standards/alto/ns-v4#",
}
XLINK = "{%s}" % ns['xlink']
ALTO = "{%s}" % ns['alto']

norm_alto_ns_re = re.compile(rb'alto/ns-v.#')

class Alto:

    def __init__(self):
        """
        The constructor.
        """

        self.tree = None
        self.insert_index = 0
        self.last_inserted_elem = None
        self.path = ""
        self.text = ""
        self.line_index_struct = {}
        self.line_index = 0

        # logging
        self.logger = logging.getLogger(__name__)
    
    def write(self, stream):
        """
        Writes the ALTO tree to stream.
        :param stream: The output stream.
        """
        stream.write(etree.tostring(self.tree.getroot(), encoding="utf-8"))

    @classmethod
    def read(cls, source):
        """
        Reads in ALTO from a given (file) source.
        :param source: ALTO (file) source.
        """
        if hasattr(source, 'read'):
            return cls.fromfile(source)
        if os.path.exists(source):
            with open(source, 'rb') as f:
                return cls.fromfile(f)

    @classmethod
    def fromfile(cls, path):
        """
        Reads in ALTO from a given file source.
        :param str path: Path to a ALTO document.
        """
        i = cls()
        i._fromfile(path)
        return i

    def _fromfile(self, path):
        """
        Reads in ALTO from a given file source.
        :param str path: Path to a ALTO document.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        self.tree = etree.XML(norm_alto_ns_re.sub(b"alto/ns-v4#", path.read()), parser)
        self.path = path

    def get_text_blocks(self):
        """
        Returns an iterator on the text block elements.
        """
        for text_block in self.tree.xpath(".//alto:TextBlock", namespaces=ns):
            yield text_block

    def get_lines_in_text_block(self, text_block):
        """
        Returns an iterator on the lines within a text block element.
        :param Element text_block: The text block element to iterate on.
        """
        for line in text_block.xpath("./alto:TextLine", namespaces=ns):
            yield line

    def get_text_in_line(self, line):
        """
        Returns the ALTO-encoded text .
        :param Element line: The line to extract the text from.
        """
        text = " ".join(element.get("CONTENT") for element in line.xpath("./alto:String", namespaces=ns))
        hyp = line.find("alto:HYP", namespaces=ns)
        if hyp is not None:
            text += hyp.get("CONTENT")
        return text

    def __compute_fuzzy_distance(self, text1, text2):
        """
        Returns a somewhat modified edit distance which respects certain
        OCR characteristics.
        :param String text1: A string.
        :param String text2: Another string.
        """
        return Levenshtein.distance(text1.translate({ord(i): None for i in '. '}), text2.translate({ord(i): None for i in '. '}))
    
    def get_best_insert_index(self, label, lower=False):
        """
        Finds the "closest" match (wrt. to Levenshtein distance)
        for a given string within the ALTO text. Returns -1 if a
        given minimal string distance is not reached.
        :param String label: The string to be placed.
        :param Boolean lower: Compute the edit distance on lowercased strings.
        """
        if lower:
            text = self.text.lower()
            label = label.lower()
        else:
            text = self.text

        if len(label) >= len(text):
            return (0, len(text))
        minimum = len(label)
        index = -1
        # the moving window
        for k in range(self.insert_index, len(text) - len(label)):
            distance = self.__compute_fuzzy_distance(label, text[k:k+len(label)])
            if distance <= minimum:
                minimum = distance
                index = k
                self.logger.debug("New best match at index %i: %s" % (index, text[index:index+len(label)].strip()))
            if distance == 0:
                break
        return (index, len(text[index:index+len(label)].strip()))

    def collect_text_nodes(self, begin, length):
        """
        Collects all paragraph and line nodes which contribute to the
        text defined by the given index 'begin' and the given length.
        :param Integer begin: The start index of the text match
        :param Integer length: The length of the text match
        """
        pars = []
        lines = []
        # iterate over all positions in the match and collect the lines and pars they are in
        for i in range(begin, begin + length):
            line = self.line_index_struct[i]
            if (not lines) or lines[-1] != line:
                lines.append(line)
                # move all lines of the match to a single paragraph
                par = line.getparent()
                if not pars:
                    pars.append(par)
                if pars[0] != par:
                    pars[0].append(line)
                    if len(par) == 0:
                        par.getparent().remove(par)
        return (pars, lines)
