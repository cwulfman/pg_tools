import io
import re
from zipfile import ZipFile
import io
from pathlib import Path
from lxml import etree
from nlp.page import Page


def fix_entities(xml_string:str) -> str:
    # Remove XML declaration to avoid ValueError
    xml_string = re.sub(r'<\?xml.*?\?>', '', xml_string, flags=re.DOTALL)
    # Replace bad entities (example: replace &shy; with actual soft hyphen)
    xml_string = xml_string.replace("&shy;", "\u00AD")
    xml_string = xml_string.replace("&quot;", "\u0022")
    return xml_string


class Epub:
    def __init__(self, zipfile_path:str) -> None:
        self.zipfile = Path(zipfile_path)
        with ZipFile(self.zipfile, mode='r') as archive:
            self.names = archive.namelist()
            self.infos = archive.infolist()

    def get_member(self, fname, format='xml'):
        with ZipFile(self.zipfile, mode='r') as archive:
            with archive.open(fname, mode='r') as binary_file:
                with io.TextIOWrapper(binary_file, encoding='utf-8') as text_file:
                    string = text_file.read()
            if format == 'xml':
                clean_data = fix_entities(string)
                return etree.fromstring(clean_data)
            else:
                return string


class Volume:
    def __init__(self):
        self._page_list = None
        self._xml = None
        

class EPubVolume(Volume):
    def __init__(self, epub_file_path):
        super().__init__()
        self.epub = Epub(epub_file_path)
        self.barcode = Path(epub_file_path).stem
        self._page_list = None

    @property
    def toc(self):
        if self._toc is None:
            self._toc = self.epub.get_member("OEBPS/toc.xhtml")
        return self._toc

    @property
    def page_list(self):
        if self._page_list is None:

            pagenames = [name for name in self.epub.names
                         if name.startswith("OEBPS/xhtml") and
                         name.endswith(".xhtml")]
            if pagenames:
                self._page_list = sorted(pagenames)
            
        return self._page_list


    def page(self, index):
        if self.page_list:
            pname = self.page_list[index]
            if pname:
                p_tree =  self.epub.get_member(pname)
                if p_tree is not None:
                    return Page(p_tree, number=index)
        

    def xml(self, greek_only=True) -> str:
        if self._xml is None:
            with io.StringIO() as buffer:
                buffer.write(f"<volume n='{self.barcode}'>\n")
                if self.page_list:
                    for i in range(0, len(self.page_list)-1):
                        if page := self.page(i):
                            page_buffer:str | None = page.xml(greek_only=greek_only)
                            if page_buffer:
                                buffer.write(page_buffer)
                buffer.write("</volume>\n")
                self._xml = buffer.getvalue()
        return self._xml


    
    def serialize(self, dir_path:Path, greek_only=True):
        file_path = (dir_path / self.barcode).with_suffix(".xml")
        with open(file_path, 'w+', encoding="utf-8") as f:
            f.write(self.xml(greek_only=greek_only))

