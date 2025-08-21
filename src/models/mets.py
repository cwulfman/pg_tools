# mets.py
#
# Models of METS objects

from pathlib import Path
import re
from lxml import etree
from models.ocr_doc import OCRPage, OCRBlock, OCRLine, OCRWord


namespaces = {
    'mets' : "http://www.loc.gov/METS/",
    'xlink' : "http://www.w3.org/1999/xlink",
    'html' : "http://www.w3.org/1999/xhtml"
    }

def fix_entities(xml_string:str) -> str:
    # Remove XML declaration to avoid ValueError
    xml_string = re.sub(r'<\?xml.*?\?>', '', xml_string, flags=re.DOTALL)
    # Replace bad entities (example: replace &shy; with actual soft hyphen)
    xml_string = xml_string.replace("&shy;", "\u00AD")
    xml_string = xml_string.replace("&", "&amp;")
    return xml_string

class Mets:
    def __init__(self, directory:Path):
        self.directory = directory

class Page(Mets):
    def __init__(self, root:etree.Element, directory:Path):
        self.root = root
        self.directory = directory
        self.fileids = self.root.xpath("mets:fptr/@FILEID", namespaces=namespaces)
        self._xml = None
        self._html = None
        self.doc = OCRPage(self.html)

    @property
    def coordOCR_file(self):
        return self.file_by_use('coordOCR')

    @property
    def text_file(self):
        return self.file_by_use('OCR')

    @property
    def image_file(self):
        return self.file_by_use('image')

    @property
    def html(self):
        if self._html is None:
            # read file into a string and fix entity references
            with open(self.coordOCR_file, 'r') as f:
                file_content = f.read()
            data = fix_entities(file_content)
            # self._html = etree.parse(data)
            if len(data) > 1:
                self._html = etree.XML(data)
        return self._html

    def file_by_use(self, use):
        files = [self.file(id) for id in self.fileids]
        file_element = [f for f in files if use in self.fileuse(f)][0]
        flocat = file_element.xpath("./mets:FLocat/@xlink:href", namespaces=namespaces)[0]
        return self.directory / flocat
            

    def file(self, fileid):
        fgroup = self.root.xpath("ancestor::mets:mets/mets:fileSec/mets:fileGrp/mets:file", namespaces=namespaces)
        file = [f for f in fgroup if f.get('ID') == fileid][0]
        return file

    def fileuse(self, file):
        return file.xpath("./parent::*/@USE", namespaces=namespaces)

    def filepath(self, fileid):
        fgroup = self.root.xpath("ancestor::mets:mets/mets:fileSec/mets:fileGrp/mets:file", namespaces=namespaces)
        file = [f for f in fgroup if f.get('ID') == fileid][0]
        return fgroup

    @property
    def physical_order(self):
        orders = self.root.xpath("@ORDER", namespaces=namespaces)
        if orders:
            return int(orders[0])

    @property
    def logical_order(self):
        orders = self.root.xpath("@ORDERLABEL", namespaces=namespaces)
        if orders:
            return orders[0]

    @property
    def text(self) -> str:
        page = ""
        
        page += f"<pb n='{self.physical_order}' facs='njp_{self.directory.stem}_{self.coordOCR_file.stem}'/>\n"
        if self.logical_order:
            page += f"<cb n='{self.logical_order}'/>\n"
            page += f"<cb n='{self.logical_order + 1}'/>\n"
        page += self.doc.text
        return page


class Volume(Mets):
    def __init__(self, directory:Path):
        self.directory = directory
        self.mets = etree.parse(list(self.directory.glob("*.xml"))[0])
        self.filepaths:dict = {}
        self.fileuses:dict = {}
        for f in list(self.mets.xpath(".//mets:fileSec//mets:file", namespaces=namespaces)):
            id = f.xpath("@ID", namespaces=namespaces)[0]
            fpath = f.xpath("./mets:FLocat/@xlink:href", namespaces=namespaces)
            use = f.xpath("parent::mets:fileGrp/@USE", namespaces=namespaces)
            self.filepaths[id] = fpath
            self.fileuses[id] = use
        self._pages = None
        self._xml = None

    def fileuse(self, id):
        """Determines the use of a file (coordOCR, OCR, or image). """

        file = self.mets.xpath("mets:fileSec/mets:fileGrp/mets:file[@ID=id]", namespaces=namespaces)
        use = file.xpath("parent::mets:fileGrp/@USE", namespaces=namespaces)
        return use[0]

    @property
    def pages(self):
        if self._pages is None:
            self._pages = [Page(div, self.directory) for div in
                            list(self.mets.xpath("//mets:div[@TYPE='page']",
                                                 namespaces=namespaces))]
        return self._pages

    @property
    def xml(self):
        if self._xml is None:
            self._xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            self._xml += '<text>\n'
            for page in self.pages:
                self._xml += f"\n{page.text}"
            self._xml += "\n</text>"
        return self._xml
