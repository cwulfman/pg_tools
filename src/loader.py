from pathlib import Path
import re
from lxml import etree
import nlp
import logging


# Configure basic logging to the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ns = {"xhtml": "http://www.w3.org/1999/xhtml"}

def fix_entities(xml_string:str) -> str:
    # Remove XML declaration to avoid ValueError
    xml_string = re.sub(r'<\?xml.*?\?>', '', xml_string, flags=re.DOTALL)
    # Replace bad entities (example: replace &shy; with actual soft hyphen)
    xml_string = xml_string.replace("&shy;", "\u00AD")
    xml_string = xml_string.replace("&quot;", "\u0022")
    return xml_string



class Loader:
    def __init__(self, voldir:Path):
        self.dir = Path(voldir)
        self.pages: dict[int,nlp.Page]  = dict()

    def load_page(self, page_file:Path):
        # tree = etree.parse(page_file)
        # clean the file's contents first
        with page_file.open('r') as pf:
            raw_data = pf.read()
        clean_data = fix_entities(raw_data)
        tree = etree.fromstring(clean_data)
        try:
            page_element =  tree.xpath("//xhtml:div[@class = 'ocr_page']", namespaces=ns)[0]
            return nlp.Page(page_element)
        except IndexError as e:
            logging.error(f"{e} file had no ocr_page element")



    def load(self):
        for page_file in self.dir.glob("*.html"):
            page_object = self.load_page(page_file)
            self.pages[int(page_file.stem)] = page_object


def flatten(a):
    res = []
    for x in a:
        if isinstance(x, list):
            res.extend(flatten(x))
        else:
            res.append(x)
    return res


loader = Loader(Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148'))
loader.load()
p1 = loader.pages[697]
left_column,right_column = nlp.split_columns(p1)
ml = nlp.merged_lines(p1)
fused_line = ml[0]
