from collections import deque
import statistics
from pathlib import Path
import re
import unicodedata
from copy import deepcopy
from lxml import etree
from dataclasses import dataclass
from typing import Iterator

ns = {"xhtml": "http://www.w3.org/1999/xhtml"}

def flatten(a):
    res = []
    for x in a:
        if isinstance(x, list):
            res.extend(flatten(x))
        else:
            res.append(x)
    return res

@dataclass(frozen=True)
class Point:
    x: int
    y: int
    

@dataclass
class BBox:
    min: Point
    max: Point

    @property
    def width(self) -> int:
        return self.max.x - self.min.x

    @property
    def height(self) -> int:
        return self.max.y - self.min.y

    @property
    def left(self):
        return self.min.x

    @property
    def right(self):
        return self.max.x - self.height

    @property
    def top(self):
        return self.min.x

    @property
    def bottom(self):
        return self.max.y
    

    def __init__(self, x_min:int, y_min:int, x_max:int, y_max:int):
        self.min = Point(x_min, y_min)
        self.max = Point(x_max, y_max)
    

class Token:
    def __init__(self, element:etree.Element) -> None:
        self.type = 'token'
        self.element = element
        self.text = self.clean_text(element.text)
        self.tail = element.tail
        bbox_string = element.get('title').split(';')[0].split(' ')[1:]
        values = [int(v) for v in bbox_string]
        # self.bbox = BBox(Point(values[0], values[1]), Point(values[3], values[4]));
        self.bbox = BBox(*values)
        self.index = None
        self.parent = None

    def __repr__(self) -> str:
        return f"Token({self.text!r})"

    def __str__(self) -> str:
        return self.text_with_ws

    @property
    def text_with_ws(self) -> str:
        if self.tail:
            return self.text + self.tail
        else:
            return self.text

    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.min.x

    @property
    def right(self):
        return self.bbox.max.x - self.bbox.height

    @property
    def top(self):
        return self.bbox.min.x

    @property
    def bottom(self):
        return self.bbox.max.y
        


    def clean_text(self,text):
        # Replace bad entities (example: replace &shy; with actual soft hyphen)
        text = text.replace("&shy;", "\u00AD")
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text
        


    def is_greek(self, threshold: float = 0.5) -> bool:
        greek_count = 0
        alpha_count = 0
        
        for char in self.text:
            alpha_count += 1
            codepoint = ord(char)
                # is it in the Greek and Coptic code block or the Extended Greek code block?
            if (0x0370 <= codepoint <= 0x03FF) or (0x1F00 <= codepoint <= 0x1FFF):
                greek_count += 1
                
        if alpha_count == 0:
                return False  # No letters at all
                
        return (greek_count / alpha_count) >= threshold


    @property
    def is_punct(self) -> bool:
        """
        Returns True if the character is punctuation based on Unicode category.
        """
        if len(self.text) != 1:
            return False
        return unicodedata.category(self.text).startswith('P')

    
       
class Line:
    def __init__(self, token_list):
        self.tokens = token_list
        # self.words = [tok for tok in self.tokens if not(tok.is_punct)]
        # calculate the BBox from the tokens
        if self.tokens:
            self.bbox = BBox(self.tokens[0].bbox.min.x,
                             self.tokens[0].bbox.min.y,
                             self.tokens[-1].bbox.max.x,
                             self.tokens[-1].bbox.max.y)
        else:
            self.bbox = BBox(0,0,0,0)



    def __str__(self):
        txt = ''
        for token in self.tokens:
            txt += token.text_with_ws
        return txt

    def __repr__(self):
        txt = ''
        for token in self.tokens:
            txt += token.text_with_ws
        return f"|{txt}|"

    @property
    def words(self):
        return [tok for tok in self.tokens if not(tok.is_punct)]

    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.min.x

    @property
    def right(self):
        return self.bbox.max.x - self.bbox.height

    @property
    def top(self):
        return self.bbox.min.x

    @property
    def bottom(self):
        return self.bbox.max.y

    @property
    def percent_greek(self):
        if len(self.words) == 0:
            return 0
        else:
            greek_words = [word for word in self.words if word.is_greek()]
            return round(100 * (len(greek_words) / len(self.words)))

    @property
    def is_greek(self) -> bool:
        return self.percent_greek > 60

    def adjacent(self, span) -> bool:
        return abs(self.top - span.top) <= 10
    


    def split(self, x):
        if len(self.tokens) > 0:
            left_line = Line(self.tokens[:x])
            right_line = Line(self.tokens[x:])
            return left_line, right_line
        else:
            return Line(), Line()
        

class Page:
    def __init__(self, tree:etree.Element, page_number):
        self.number = page_number
        self.root = tree.xpath("//xhtml:div[@class='ocr_page']", namespaces=ns)[0]
        bbox_string = self.root.get('title').split(';')[0].split(' ')[1:]
        values = [int(v) for v in bbox_string]
        self.bbox = BBox(*values)

        self.lines = []
        source_lines = self.root.xpath(".//xhtml:span[@class='ocr_line']",  namespaces=ns)
        for source_line in source_lines:
            source_tokens = source_line.xpath(".//xhtml:span[@class='ocrx_word']", namespaces=ns)
            self.lines.append(Line([Token(x) for x in source_tokens]))
        self.column_numbers = self.extract_column_numbers()
        self.running_head = self.extract_running_head()
        self.remove_header()


    def analyze_layout(self):
        pass
        
    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.min.x

    @property
    def right(self):
        return self.bbox.max.x

    @property
    def percent_greek(self):
        if len(self.words) == 0:
            return 0
        else:
            greek_words = [word for word in self.words if word.is_greek()]
            return round(100 * (len(greek_words) / len(self.words)))

    @property
    def midline(self):
        return self.width / 2

    @property
    def header_lines(self):
        return self.lines_adjacent(self.lines[0])

    @property
    def header(self):
        return self.lines_adjacent(self.lines[0])

    def lines_adjacent(self, a_line):
        return [line for line in self.lines if abs(a_line.bottom - line.bottom) <= 10]

    def lines_aligned_left(self, x, padding=30):
        # return [line for line in self.lines if abs(line.left - x) <= padding]
        return [line for line in self.lines if line.left <= x]

    @property
    def left_column(self):
        left_lines = self.lines_aligned_left(self.midline / 2)
        # drop the first line; it is the header
        # return left_lines[1:]
        return Column(left_lines, 'left', self.column_numbers.get('left'))

    @property
    def right_column(self):
        return Column([line for line in self.lines if abs(line.left - self.midline) <= 300], 'right', self.column_numbers.get('right'))

    @property
    def greek_column(self):
        left_column = self.left_column
        if left_column and percent_greek(left_column.tokens) > .5:
            return left_column
        else:
            right_column = self.right_column
            if right_column and percent_greek(right_column.tokens) > .5:
                return right_column
            

    def extract_column_numbers(self):
        col_nums = {}
        header_string = ' '.join([str(line) for line in self.header_lines])
        p = re.compile(r'^(\d+)\D+(\d+).*$')
        m = p.match(header_string)
        if m:
            col_nums['left'] = m.group(1)
            col_nums['right'] = m.group(2)
        return col_nums

    def extract_running_head(self):
        header_string = ' '.join([str(line) for line in self.header_lines])
        p = re.compile(r'^\d+(\D+)\d+.*$')
        m = p.match(header_string)
        if m:
            return m.group(1)
        else:
            return None

    def remove_header(self):
        for line in self.header_lines:
            self.lines.remove(line)
        return self.lines


    def display(self):
        for i,line in enumerate(self.lines):
            print(f"{i}\t{line}")


    @property
    def fused_lines(self):
        return [line for line in self.left_column.lines if len(line.tokens) > 4 and line.right > self.midline]


    def fix_fused_line(self, fused_line):
        split_point = round(len(fused_line.tokens) / 2)
        left_line, right_line = fused_line.split(split_point)
        if right_line.is_greek:
            try:
                while left_line.words[-1].is_greek():
                    self.shift_word_right(left_line, right_line)
            except IndexError:
                breakpoint()
        else:
            try:
                while right_line.words[0].is_greek():
                    self.shift_word_left(left_line, right_line)
            except IndexError:
                breakpoint()

        idx =self.lines.index(fused_line)
        del(self.lines[idx])
        self.lines.insert(idx, right_line)
        self.lines.insert(idx, left_line)
        
        
    def fix_fused_lines(self):
        fused_lines = self.fused_lines
        for fl in fused_lines:
            self.fix_fused_line(fl)

    def shift_word_right(self, line1, line2):
        word = line1.words[-1]
        index = line1.tokens.index(word)
        while len(line1.tokens) != index:
            tok = line1.tokens.pop()
            # line2.tokens.appendleft(tok)
            line2.tokens.insert(0, tok)

        
    def shift_word_left(self, line1, line2):
        word = line1.words[0]
        index = line1.tokens.index(word)
        while len(line1.tokens) != index:
            tok = line1.tokens.pop(0)
            line2.tokens.append(tok)


class Column:
    def __init__(self, line_list, side, column_number):
        self.lines = line_list
        self.number = column_number
        self.side = side
        self.tokens = flatten([line.tokens for line in self.lines])
        # self.words = [tok for tok in self.tokens if not(tok.is_punct)]
        # calculate the BBox from the tokens
        if self.tokens:
            self.bbox = BBox(self.tokens[0].bbox.min.x,
                             self.tokens[0].bbox.min.y,
                             self.tokens[-1].bbox.max.x,
                             self.tokens[-1].bbox.max.y)
        else:
            self.bbox = BBox(0,0,0,0)

    @property
    def words(self):
        return [tok for tok in self.tokens if not(tok.is_punct)]

    def __str__(self):
        txt = '<cb'
        if self.number:
            txt +=  f"n='{self.number}'/>"
        else:
            txt += "/>\n"

        for line in self.lines:
            txt += f"{str(line)}\n"
        return txt
        
        

        
def percent_greek(tok_list):
    if len(tok_list) == 0:
        return 0
    else:
        tok_count = 0
        greek_count = 0
        for tok in tok_list:
            tok_count +=1
            if tok.is_greek():
                greek_count += 1
        return greek_count / tok_count
    


def fix_entities(xml_string:str) -> str:
    # Remove XML declaration to avoid ValueError
    xml_string = re.sub(r'<\?xml.*?\?>', '', xml_string, flags=re.DOTALL)
    # Replace bad entities (example: replace &shy; with actual soft hyphen)
    xml_string = xml_string.replace("&shy;", "\u00AD")
    xml_string = xml_string.replace("&quot;", "\u0022")
    return xml_string
        

def load_page_file(page_file:Path):
    with page_file.open('r') as pf:
        raw_data = pf.read()
        clean_data = fix_entities(raw_data)
        tree = etree.fromstring(clean_data)
    return tree





pfile = Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148/00000102.html')
page_root = load_page_file(pfile)

p2 = Page(page_root, 102)
