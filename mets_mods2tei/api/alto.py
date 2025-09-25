# -*- coding: utf-8 -*-

from lxml import etree
from rapidfuzz.distance import Levenshtein
from pathlib import Path
from typing import Optional, List, Dict, Union, IO
import logging
import re

NS = {
    'xlink': "http://www.w3.org/1999/xlink",
    'alto': "http://www.loc.gov/standards/alto/ns-v4#",
}
XLINK = "{%s}" % NS['xlink']
ALTO = "{%s}" % NS['alto']

norm_alto_ns_re = re.compile(rb'alto/ns-v.#')


class Alto:
    """A class to handle ALTO (Analyzed Layout and Text Object) files."""

    def __init__(self) -> None:
        """
        Initialize the Alto instance.

        Sets up the internal data structures and default values for handling ALTO files.
        """
        self.tree: Optional[etree._ElementTree] = None
        self.insert_index: int = 0
        self.last_inserted_elem: Optional[etree._Element] = None
        self.path: str = ""
        self.text: str = ""
        self.line_index_struct: Dict[int, str] = {}
        self.line_index: int = 0

        # logging
        self.logger = logging.getLogger(__name__)

    def write(self, stream: IO) -> None:
        """
        Write the ALTO tree to a stream.

        Args:
            stream: The output stream to write the ALTO tree to.
        """
        stream.write(etree.tostring(self.tree.getroot(), encoding="utf-8"))

    @classmethod
    def read(cls, source: Union[str, IO]) -> 'Alto':
        """
        Read an ALTO file from a given source.

        Args:
            source: The ALTO file source, which can be a file path or a file-like object.

        Returns:
            Alto: An instance of the Alto class.
        """
        if hasattr(source, 'read'):
            return cls.fromfile(source)
        if Path(source).exists():
            with open(source, 'rb') as f:
                return cls.fromfile(f)

    @classmethod
    def fromfile(cls, path: Union[str, IO]) -> 'Alto':
        """
        Read an ALTO file from a given file path.

        Args:
            path (str): The path to the ALTO file.

        Returns:
            Alto: An instance of the Alto class.
        """
        instance = cls()
        instance._fromfile(path)
        return instance

    def _fromfile(self, path: Union[str, IO]) -> None:
        """
        Parse an ALTO file from a given file path.

        Args:
            path (str): The path to the ALTO file.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        self.tree = etree.XML(norm_alto_ns_re.sub(b"alto/ns-v4#", path.read()), parser)
        self.path = path

    @classmethod
    def frombytes(cls, content):
        """
        Reads in ALTO from a given byte string.
        :param bytes content: Content of a ALTO document.
        """
        i = cls()
        i._frombytes(content)
        return i

    def _frombytes(self, content):
        """
        Reads in ALTO from a given byte string.
        :param bytes content: Content of a ALTO document.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        self.tree = etree.XML(norm_alto_ns_re.sub(b"alto/ns-v4#", content), parser)

    def get_text_blocks(self) -> List[etree._Element]:
        """
        Get all text blocks from the ALTO file.

        Returns:
            List[etree._Element]: A list of text block elements.
        """
        return self.tree.xpath('//alto:TextBlock', namespaces=NS)

    def get_lines_in_text_block(self, text_block: etree._Element) -> List[etree._Element]:
        """
        Get all lines in a given text block.

        Args:
            text_block (etree._Element): The text block element.

        Returns:
            List[etree._Element]: A list of line elements.
        """
        return text_block.xpath('.//alto:TextLine', namespaces=NS)

    def get_text_in_line(self, line: etree._Element) -> str:
        """
        Get the text content of a given line.

        Args:
            line (etree._Element): The line element.

        Returns:
            str: The text content of the line.
        """
        text = ' '.join(line.xpath('.//alto:String/@CONTENT', namespaces=NS))
        hyp = line.find("alto:HYP", namespaces=NS)
        if hyp is not None:
            text += hyp.get("CONTENT")
        return text

    def __compute_fuzzy_distance(self, text1: str, text2: str) -> int:
        """
        Compute the fuzzy distance between two strings.

        Args:
            text1 (str): The first string.
            text2 (str): The second string.

        Returns:
            int: The Levenshtein distance between the two strings.
        """
        text1 = text1.translate({ord(i): None for i in '. '})
        text2 = text2.translate({ord(i): None for i in '. '})
        return Levenshtein.distance(text1, text2)

    def get_best_insert_index(self, label: str, lower: bool = False) -> int:
        """
        Get the best insert index for a given label.

        Args:
            label (str): The label to find the best insert index for.
            lower (bool): Whether to convert the label to lowercase.

        Returns:
            int: The best insert index.
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
