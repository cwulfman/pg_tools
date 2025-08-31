import io
import logging
import re
from pathlib import Path
from lxml import etree
from models.mets import MetsVolume, MetsPage
from nlp.page import Page, BlankPage
from nlp.utils import ns



# Configure basic logging to the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def fix_entities(xml_string:str) -> str:
    # Remove XML declaration to avoid ValueError
    xml_string = re.sub(r'<\?xml.*?\?>', '', xml_string, flags=re.DOTALL)
    # Replace bad entities (example: replace &shy; with actual soft hyphen)
    xml_string = xml_string.replace("&shy;", "\u00AD")
    xml_string = xml_string.replace("&quot;", "\u0022")
    return xml_string

def new_page(tree:etree.Element):
    root = tree.xpath("//xhtml:div[@class='ocr_page']", namespaces=ns)[0]
    children = [child for child in root if child.get('class') is not None]
    if children:
        return 

class Loader:
    def __init__(self, volpath):
        self.volpath = volpath
        self.metsvol = MetsVolume(volpath)

    def load_page(self, page_num):
        mets_page:MetsPage = self.metsvol.page(page_num)
        coordOCR_file = self.load_page_file(mets_page.coordOCR_file)
        if coordOCR_file is not None:
            exception_tags = ['BLANK', 'FRONT_COVER', 'BACK_COVER', "IMAGE_ON_PAGE"]
            if any([tag for tag in exception_tags if tag in mets_page.tags]):
                nlp_page = BlankPage(coordOCR_file, page_num)
            else:
                root = coordOCR_file.xpath("//xhtml:div[@class='ocr_page']", namespaces=ns)[0]
                children = [child for child in root if child.get('class') is not None]
                if len(children) > 0:
                    nlp_page = Page(coordOCR_file, page_num)
                else:
                    nlp_page = BlankPage(coordOCR_file, page_num)

            return PgPage(mets_page, nlp_page)


    def load_page_file(self,page_file:Path):
        with page_file.open('r') as pf:
            raw_data = pf.read()
            clean_data = fix_entities(raw_data)
            if clean_data:
                tree = etree.fromstring(clean_data)
                return tree



class PgVolume:
    def __init__(self, volpath:Path):
        self.metsvol = MetsVolume(volpath)
        self.loader = Loader(volpath)
        self._pages = {}
        self._xml = None


    def page(self, page_num):
        if self._pages.get(page_num) is None:
            self._pages[page_num] = self.loader.load_page(page_num)
        return self._pages[page_num]
    
    @property
    def page_list(self):
        return self.metsvol.page_list

    @property
    def barcode(self):
        return self.metsvol.id[0]

    def chapter_starts(self):
        starts = {}
        for i in self.metsvol.page_index:
            mets_page = self.metsvol.page(i)
            if 'CHAPTER_START' in mets_page.tags:
                starts[i] = self.page(i)
        return starts

    def chapter_titles(self):
        chapter_starts = self.chapter_starts()
        title_info = {}
        for k,page in chapter_starts.items():
            titles = page._nlp_page.titles
            metadata = { "titles" : titles, "page_num" : k }
            if cnums := page.column_numbers:
                metadata["left_column"] =  cnums['left']
                metadata["right_column"] =  cnums['right']
            title_info[k] = metadata
        return title_info

    def works_xml(self):
        chapter_starts = self.chapter_starts()
        txt = '<?xml version="1.0" encoding="UTF-8"?>\n'
        txt += "<works>\n"
        for k,page in chapter_starts.items():
            titles = page._nlp_page.titles
            names = page._nlp_page.names_in_titles
            start = None
            if page.column_numbers:
                start = page.column_numbers.get('left')
            volume = self.metsvol.id[0]
            txt += f"<work volume='{volume}' "
            txt += f"start='{start}'"
            txt += ">\n"
            for name in names:
                txt += f"<name>{str(name).strip()}</name>\n"
            for title in titles:
                txt += f"<title>{str(title).strip()}</title>\n"
            txt += "</work>\n"
        txt += "</works>"
        return txt

    
    def xml(self, greek_only=True) -> str:
        if self._xml is None:
            with io.StringIO() as buffer:
                buffer.write(f"<volume n='{self.barcode}'>\n")
                for pagenum in self.page_list:
                    page = self.page(pagenum)
                    page_buffer = page.xml(greek_only = greek_only)
                    buffer.write(page_buffer)
                buffer.write("</volume>\n")
                self._xml = buffer.getvalue()
        return self._xml


        

    def serialize(self, dir_path:Path, greek_only=True):
        file_path = (dir_path / self.barcode).with_suffix(".xml")
        with open(file_path, 'w+', encoding="utf-8") as f:
            f.write(self.xml(greek_only=greek_only))
            


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
    def type(self):
        return self._nlp_page.type

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


    def xml(self, greek_only=True):
        self._nlp_page.repair_fused_lines()
        with io.StringIO() as buffer:
            buffer.write(f"<page n='{self.physical_order}'")
            if self._nlp_page.running_head:
                head_txt = ' '.join(str(line) for line in self._nlp_page.running_head)
                buffer.write(f"running_head='{head_txt.strip()}'")
            buffer.write(">\n")
            if greek_only:
                for column in self._nlp_page.greek_columns:
                    buffer.write("<column ")
                    if column.side == 'left' and self._mets_page.logical_order:
                        buffer.write(f"n = '{self._mets_page.logical_order}'")
                    elif column.side == 'right' and self._mets_page.logical_order:
                        try:
                            buffer.write(f"n= '{str(int(self._mets_page.logical_order) + 1)}'")
                        except ValueError:
                            pass
                    else:
                        pass
                    buffer.write(">\n")
                    buffer.write(str(column))
                    buffer.write("\n</column>\n")
            else:
                if self._nlp_page.left_column and self._mets_page.logical_order:
                    buffer.write(f"<column n='{self._mets_page.logical_order}'>\n")
                    buffer.write(str(self._nlp_page.left_column))
                    buffer.write("\n</column>\n")
                if self._nlp_page.right_column and self._mets_page.logical_order:
                    buffer.write(f"<column n='{int(self._mets_page.logical_order) + 1}'>\n")
                    buffer.write(str(self._nlp_page.right_column))
                    buffer.write("\n></column>\n")
                
            buffer.write("</page>\n")
            content = buffer.getvalue()
        return content


    def serialize(self, f, greek_only=True):
        f.write(self.xml(greek_only=greek_only))

        
        
# volpath = Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148')
# vol = PgVolume(volpath)


# p71 = vol.page(71)._nlp_page
# p97 = vol.page(97)._nlp_page

# volpath2 = Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007877465')
# vol2 = PgVolume(volpath2)


# p41 = vol2.page(41)._nlp_page
# p119 = vol2.page(119)._nlp_page

# ctitles = vol2.chapter_titles()
# works = vol2.works_xml()


volpath = Path("/Users/wulfmanc/Desktop/patrologia_graeca/32101077772786")
vol = PgVolume(volpath)

