# -*- coding: utf-8 -*-

from lxml import etree

import os

ns = {
     'mets': "http://www.loc.gov/METS/",
     'mods': "http://www.loc.gov/mods/v3",
     'xlink' : "http://www.w3.org/1999/xlink",
}
METS = "{%s}" % ns['mets']
XLINK = "{%s}" % ns['xlink']

class Mets:

    def __init__(self):
        """
        The constructor.
        """

        self.tree = None

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

    def get_main_title(self):
        """
        Returns the main title of the work represented
        by the METS instance.
        """
        # TODO: Check whether the first dmdSec always refers to the volume title,
        # alternatively identify the corresponding dmdSec via <structMap type="Logical" />
        return self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:titleInfo/mods:title", namespaces=ns)[0].text

    def get_sub_titles(self):
        """
        Returns the main title of the work represented
        by the METS instance.
        """
        # TODO: Check whether the first dmdSec always refers to the volume title,
        # alternatively identify the corresponding dmdSec via <structMap type="Logical" />
        return [text.text for text in self.tree.xpath("//mets:dmdSec[1]//mods:mods/mods:titleInfo/mods:subTitle", namespaces=ns)]
