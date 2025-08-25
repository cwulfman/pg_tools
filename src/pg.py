import re
from pathlib import Path
from lxml import etree
from models.mets import MetsVolume, MetsPage
from nlp.page import Page, BlankPage


def fix_entities(xml_string:str) -> str:
    # Remove XML declaration to avoid ValueError
    xml_string = re.sub(r'<\?xml.*?\?>', '', xml_string, flags=re.DOTALL)
    # Replace bad entities (example: replace &shy; with actual soft hyphen)
    xml_string = xml_string.replace("&shy;", "\u00AD")
    xml_string = xml_string.replace("&quot;", "\u0022")
    return xml_string

class Loader:
    def __init__(self, volpath):
        self.volpath = volpath
        self.metsvol = MetsVolume(volpath)

    def load_page(self, page_num):
        mets_page:MetsPage = self.metsvol.page(page_num)
        coordOCR_file = self.load_page_file(mets_page.coordOCR_file)
        exception_tags = ['BLANK', 'FRONT_COVER', 'BACK_COVER']
        if any([tag for tag in exception_tags if tag in mets_page.tags]):
            nlp_page = BlankPage(coordOCR_file, page_num)
        else:
            nlp_page = Page(coordOCR_file, page_num)
        return PgPage(mets_page, nlp_page)


    def load_page_file(self,page_file:Path):
        with page_file.open('r') as pf:
            raw_data = pf.read()
            clean_data = fix_entities(raw_data)
            tree = etree.fromstring(clean_data)
        return tree



class PgVolume:
    def __init__(self, volpath:Path):
        self.metsvol = MetsVolume(volpath)
        self.loader = Loader(volpath)
        self._pages = {}


    def page(self, page_num):
        if self._pages.get(page_num) is None:
            self._pages[page_num] = self.loader.load_page(page_num)
        return self._pages[page_num]

    def chapter_starts(self):
        starts = {}
        for i in self.metsvol.page_index:
            mets_page = self.metsvol.page(i)
            if 'CHAPTER_START' in mets_page.tags:
                starts[i] = self.page(i)
        return starts
            


class PgPage:
    def __init__(self, mets_page, nlp_page):
        self._mets_page = mets_page
        self._nlp_page = nlp_page

    def __repr__(self):
        if self.column_numbers:
            return f"<Page {self.physical_order} [{self.column_numbers['left']}-{self.column_numbers['right']}]>"
        else:
            return f"<Page {self.physical_order}>"

    @property
    def physical_order(self):
        return self._mets_page.physical_order

    @property
    def tags(self):
        return self._mets_page.tags

    @property
    def column_numbers(self):
        colnums = {}
        if self._mets_page.logical_order:
            colnums['left'] = int(self._mets_page.logical_order)
            colnums['right'] = int(self._mets_page.logical_order) + 1
        return colnums

    @property
    def columns(self):
        left_column, right_column = self._nlp_page.columns()
        left_column.number = self.column_numbers['left']
        right_column.number = self.column_numbers['right']
        return left_column, right_column


    def serialize(self, greek_only=True):
        self._nlp_page.repair_fused_lines()
        txt = ''
        txt += f"<pb n='{self.physical_order}' "
        if self._nlp_page.running_head:
            txt += f"ed='{self._nlp_page.running_head}' "
        txt += "/>\n"
        left_column, right_column = self._nlp_page.columns

        return txt
        
        
volpath = Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148')
vol = PgVolume(volpath)


p71 = vol.page(71)._nlp_page
p97 = vol.page(97)._nlp_page

